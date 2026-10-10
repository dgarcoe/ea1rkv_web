"""Persistent outbox. No HTTP requests are made in the publishing request."""
import json
from datetime import timedelta
from html import escape
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from django.utils.html import strip_tags
from wagtail.signals import page_published

from .models import BlogPage, TelegramDelivery


@receiver(page_published, sender=BlogPage, dispatch_uid="blog_telegram_outbox")
def enqueue(sender, instance, **kwargs):
    if (settings.TELEGRAM_ENABLED and instance.announce_telegram
            and instance.locale.language_code == "es"
            and instance.first_published_at == instance.last_published_at
            and BlogPage.objects.live().public().filter(pk=instance.pk).exists()):
        TelegramDelivery.objects.get_or_create(
            page=instance, defaults={"chat_id": settings.TELEGRAM_CHAT_ID}
        )


def send_pending(limit=20):
    if not settings.TELEGRAM_ENABLED:
        return
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        raise ValueError("Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")
    # A crashed worker may have delivered a message. Never retry it blindly.
    TelegramDelivery.objects.filter(
        status="sending", updated_at__lt=timezone.now() - timedelta(minutes=5)
    ).update(status="uncertain", error="Envío interrumpido: comprueba el canal antes de reintentar")
    ids = list(TelegramDelivery.objects.filter(
        status="pending", next_attempt__lte=timezone.now()
    ).order_by("pk").values_list("pk", flat=True)[:limit])
    for pk in ids:
        # Atomic claim: simultaneous workers cannot send the same row.
        if not TelegramDelivery.objects.filter(pk=pk, status="pending").update(
                status="sending", updated_at=timezone.now()):
            continue
        delivery = TelegramDelivery.objects.select_related("page", "page__locale").get(pk=pk)
        delivery.attempts += 1
        try:
            page = delivery.page
            if (not page.announce_telegram or page.locale.language_code != "es"
                    or not BlogPage.objects.live().public().filter(pk=page.pk).exists()):
                delivery.status = "cancelled"
                delivery.error = "Entrada retirada, privada o anuncio desactivado"
            else:
                url = page.full_url
                if not url or urlsplit(url).scheme != "https":
                    raise ValueError("La página necesita una URL pública HTTPS en Wagtail Sites")
                text = (f"<b>{escape(page.title[:200])}</b>\n\n"
                        f"{escape(strip_tags(page.intro)[:300])}")
                payload = {"chat_id": delivery.chat_id, "parse_mode": "HTML",
                           "reply_markup": {"inline_keyboard": [[{"text": "Leer en la web", "url": url}]]}}
                method = "sendMessage"
                payload["text"] = text + f'\n\n<a href="{escape(url, quote=True)}">Leer en la web</a>'
                if page.header_image_id:
                    image_url = page.header_image.get_rendition("max-1280x1280").url
                    if image_url.startswith("/"):
                        origin = urlsplit(url)
                        image_url = f"{origin.scheme}://{origin.netloc}{image_url}"
                    payload.pop("text")
                    payload.update(photo=image_url, caption=text)
                    method = "sendPhoto"
                request = Request(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}",
                    data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"},
                )
                try:
                    with urlopen(request, timeout=30) as response:
                        result = json.load(response)
                except HTTPError as exc:
                    # Do not log exception URLs: they contain the bot token.
                    result = json.loads(exc.read())
                if result.get("ok"):
                    delivery.status = "sent"
                    delivery.message_id = result["result"]["message_id"]
                    delivery.error = ""
                elif result.get("error_code") == 429 and delivery.attempts < 5:
                    delay = max(60, int(result.get("parameters", {}).get("retry_after", 60)))
                    delivery.status = "pending"
                    delivery.next_attempt = timezone.now() + timedelta(seconds=delay)
                    delivery.error = "Límite temporal de Telegram; reintento programado"
                else:
                    delivery.status = "failed"
                    delivery.error = f"Telegram rechazó el envío (código {result.get('error_code', 'desconocido')})"
        except ValueError:
            delivery.status = "failed"
            delivery.error = "Revisa la URL pública y la respuesta de Telegram"
        except Exception:
            delivery.status = "uncertain"
            delivery.error = "Sin confirmación: comprueba el canal antes de reintentar"
        delivery.save()
