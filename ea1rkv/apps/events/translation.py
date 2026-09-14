"""Automatic language copies for agenda activities."""

from django.conf import settings
from django.db import transaction
from wagtail.models import Locale, Site

from .models import EventPage


@transaction.atomic
def replicate_event_translations(page):
    """Publish missing translations copied from the primary-language event."""
    if not isinstance(page, EventPage):
        return []

    site = Site.objects.filter(is_default_site=True).first()
    if site is None or page.locale_id != site.root_page.locale_id:
        return []

    available_codes = {code for code, _label in settings.LANGUAGES}
    created = []
    for locale in Locale.objects.filter(language_code__in=available_codes).exclude(
        pk=page.locale_id
    ):
        if EventPage.objects.filter(
            translation_key=page.translation_key, locale=locale
        ).exists():
            continue
        if not page.get_parent().get_translations(inclusive=True).filter(
            locale=locale
        ).exists():
            continue

        translated = page.copy_for_translation(locale, copy_parents=False)
        translated.save_revision().publish()
        created.append(translated)

    return created
