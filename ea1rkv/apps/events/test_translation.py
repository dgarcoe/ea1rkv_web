from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from wagtail.models import Locale

from ea1rkv.apps.events.models import EventIndexPage, EventPage
from ea1rkv.apps.events.translation import replicate_event_translations
from ea1rkv.apps.home.models import HomePage


class EventTranslationTests(TestCase):
    def setUp(self):
        call_command("setup_radioclub", stdout=StringIO())
        self.home = HomePage.objects.get()
        self.agenda = EventIndexPage.objects.get()

    def test_missing_translations_are_created_once_and_published(self):
        english, _ = Locale.objects.get_or_create(language_code="en")
        self.home.copy_for_translation(english)
        self.agenda.copy_for_translation(english)
        event = self.agenda.add_child(
            instance=EventPage(
                title="Reunión mensual",
                slug="reunion-mensual",
                start_date="2026-01-02",
                intro="Contenido para traducir",
            )
        )
        event.save_revision().publish()

        translated = EventPage.objects.get(
            translation_key=event.translation_key, locale=english
        )
        self.assertTrue(translated.live)
        self.assertEqual(translated.intro, "Contenido para traducir")

        self.assertEqual(replicate_event_translations(event), [])
        self.assertEqual(
            EventPage.objects.filter(translation_key=event.translation_key).count(), 2
        )

    def test_translation_does_not_create_further_copies(self):
        english, _ = Locale.objects.get_or_create(language_code="en")
        translated = EventPage(locale=english)
        self.assertEqual(replicate_event_translations(translated), [])

    def test_setup_backfills_events_published_before_target_locale(self):
        event = self.agenda.add_child(
            instance=EventPage(
                title="Actividad existente",
                slug="actividad-existente",
                start_date="2026-02-01",
                intro="Texto inicial",
            )
        )
        event.save_revision().publish()
        english, _ = Locale.objects.get_or_create(language_code="en")
        self.home.copy_for_translation(english)

        call_command("setup_radioclub", stdout=StringIO())

        self.assertTrue(
            EventPage.objects.filter(
                translation_key=event.translation_key,
                locale=english,
                live=True,
            ).exists()
        )
