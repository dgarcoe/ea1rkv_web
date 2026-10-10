import json
from io import StringIO, BytesIO
from unittest.mock import patch, PropertyMock, Mock
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from wagtail.models import Locale, PageViewRestriction

from .models import BlogIndexPage, BlogPage, TelegramDelivery
from .telegram import send_pending


@override_settings(TELEGRAM_ENABLED=True, TELEGRAM_BOT_TOKEN="secret", TELEGRAM_CHAT_ID="@test")
class TelegramTests(TestCase):
    def setUp(self):
        call_command("setup_radioclub", stdout=StringIO())
        self.page = BlogIndexPage.objects.first().add_child(instance=BlogPage(
            title="Radio & Vigo", slug="telegram-test", intro="Resumen <b>radio</b>",
            body=[], announce_telegram=True))

    def publish(self):
        self.page.save_revision().publish()
        self.page.refresh_from_db()

    def test_only_first_publication_and_no_network_in_request(self):
        with patch("ea1rkv.apps.blog.telegram.urlopen") as http:
            self.page.save_revision()
            self.assertFalse(TelegramDelivery.objects.exists())
            self.publish()
            self.publish()
            http.assert_not_called()
        self.assertEqual(TelegramDelivery.objects.count(), 1)

    def test_unchecked_first_publication_not_sent_later(self):
        self.page.announce_telegram = False
        self.publish()
        self.page.announce_telegram = True
        self.publish()
        self.assertFalse(TelegramDelivery.objects.exists())

    def test_translations_and_private_pages_excluded(self):
        self.page.locale = Locale.objects.get_or_create(language_code="en")[0]
        self.publish()
        self.assertFalse(TelegramDelivery.objects.exists())

    def test_private_page_not_queued(self):
        PageViewRestriction.objects.create(page=self.page, restriction_type="password", password="test")
        self.publish()
        self.assertFalse(TelegramDelivery.objects.exists())

    @override_settings(TELEGRAM_ENABLED=False)
    def test_disabled(self):
        self.publish()
        self.assertFalse(TelegramDelivery.objects.exists())

    def test_success_and_no_duplicate(self):
        self.publish()
        with patch.object(BlogPage, "full_url", new_callable=PropertyMock, return_value="https://ea1rkv.com/es/blog/test/"), patch(
            "ea1rkv.apps.blog.telegram.urlopen", return_value=BytesIO(b'{"ok":true,"result":{"message_id":42}}')
        ) as http:
            send_pending()
            send_pending()
            http.assert_called_once()
            payload = json.loads(http.call_args.args[0].data)
            self.assertIn("Radio &amp; Vigo", payload["text"])
            self.assertNotIn("<b>radio", payload["text"])
        row = TelegramDelivery.objects.get()
        self.assertEqual((row.status, row.message_id), ("sent", 42))

    def test_timeout_requires_manual_retry(self):
        self.publish()
        with patch.object(BlogPage, "full_url", new_callable=PropertyMock, return_value="https://ea1rkv.com/test/"), patch(
            "ea1rkv.apps.blog.telegram.urlopen", side_effect=TimeoutError("secret")
        ) as http:
            send_pending()
            send_pending()
            http.assert_called_once()
        row = TelegramDelivery.objects.get()
        self.assertEqual(row.status, "uncertain")
        self.assertNotIn("secret", row.error)
        call_command("telegram_worker", retry=row.pk, stdout=StringIO())
        row.refresh_from_db()
        self.assertEqual(row.status, "pending")

    def test_photo_uses_public_absolute_url(self):
        self.publish()
        image = Mock()
        image.get_rendition.return_value.url = "/media/images/cover.jpg"
        with patch.object(BlogPage, "full_url", new_callable=PropertyMock, return_value="https://ea1rkv.com/es/blog/test/"), patch.object(
            BlogPage, "header_image_id", new_callable=PropertyMock, return_value=1
        ), patch.object(BlogPage, "header_image", new_callable=PropertyMock, return_value=image), patch(
            "ea1rkv.apps.blog.telegram.urlopen", return_value=BytesIO(b'{"ok":true,"result":{"message_id":43}}')
        ) as http:
            send_pending()
            payload = json.loads(http.call_args.args[0].data)
            self.assertEqual(payload["photo"], "https://ea1rkv.com/media/images/cover.jpg")
            self.assertIn("caption", payload)
            self.assertTrue(http.call_args.args[0].full_url.endswith("/sendPhoto"))

    def test_rate_limit_is_delayed(self):
        self.publish()
        with patch.object(BlogPage, "full_url", new_callable=PropertyMock, return_value="https://ea1rkv.com/test/"), patch(
            "ea1rkv.apps.blog.telegram.urlopen", return_value=BytesIO(b'{"ok":false,"error_code":429,"parameters":{"retry_after":120}}')
        ) as http:
            send_pending()
            send_pending()
            http.assert_called_once()
        row = TelegramDelivery.objects.get()
        self.assertEqual(row.status, "pending")
        self.assertGreater(row.next_attempt, timezone.now())

    def test_withdrawn_page_cancelled(self):
        self.publish()
        self.page.unpublish()
        with patch("ea1rkv.apps.blog.telegram.urlopen") as http:
            send_pending()
            http.assert_not_called()
        self.assertEqual(TelegramDelivery.objects.get().status, "cancelled")

    def test_interrupted_claim_is_not_resent(self):
        self.publish()
        TelegramDelivery.objects.update(status="sending", updated_at=timezone.now()-timedelta(minutes=6))
        with patch("ea1rkv.apps.blog.telegram.urlopen") as http:
            send_pending()
            http.assert_not_called()
        self.assertEqual(TelegramDelivery.objects.get().status, "uncertain")
