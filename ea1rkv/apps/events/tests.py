from datetime import timedelta
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from wagtail.models import Locale

from ea1rkv.apps.events.models import EventIndexPage, EventPage
from ea1rkv.apps.home.models import HomePage


class AgendaTests(TestCase):
    def test_callsigns_in_calendar_and_listing(self):
        from ea1rkv.apps.club.models import CallsignsPage, SpecialCallsignPage
        from wagtail.models import PageViewRestriction

        today = timezone.localdate()
        parent = CallsignsPage.objects.get()
        callsign = parent.add_child(instance=SpecialCallsignPage(
            title="Special", slug="special", callsign="EGTEST",
            start_date=today-timedelta(days=2), end_date=today+timedelta(days=2),
        ))
        callsign.save_revision().publish()
        response = self.client.get(self.agenda.url + "?type=callsign")
        self.assertContains(response, "EGTEST")
        self.assertEqual(list(response.context["events"]), [callsign])
        day = next(d for week in response.context["calendar_weeks"] for d in week if d["date"] == today)
        self.assertEqual(day["items"], [callsign])
        response = self.client.get(self.agenda.url + "?month=invalid")
        self.assertEqual(response.status_code, 200)
        PageViewRestriction.objects.create(page=callsign, restriction_type="login")
        self.assertNotContains(self.client.get(self.agenda.url), "EGTEST")

    def setUp(self):
        call_command("setup_radioclub", stdout=StringIO())
        self.agenda = EventIndexPage.objects.get()

    def test_current_multiday_event_and_archive(self):
        today = timezone.localdate()
        active = self.agenda.add_child(instance=EventPage(
            title="Actividad", slug="actividad", start_date=today-timedelta(days=2),
            end_date=today+timedelta(days=1), intro="Actividad en curso",
        ))
        past = self.agenda.add_child(instance=EventPage(
            title="Anterior", slug="anterior", start_date=today-timedelta(days=5),
            intro="Actividad anterior",
        ))
        active.save_revision().publish()
        past.save_revision().publish()
        response = self.client.get(self.agenda.url)
        self.assertEqual(list(response.context["events"]), [active])
        self.assertFalse(active.is_past)
        self.assertContains(response, "Actividad en curso")
        response = self.client.get(self.agenda.url + "?past=true")
        self.assertEqual(list(response.context["events"]), [past])
        response = self.client.get(active.url)
        self.assertEqual(response.status_code, 200)

    def test_invalid_dates(self):
        event = EventPage(title="Invalid", start_date=timezone.localdate(),
                          end_date=timezone.localdate()-timedelta(days=1))
        with self.assertRaises(ValidationError):
            event.clean()

    def test_setup_preserves_content_and_links_translations(self):
        home = HomePage.objects.get()
        english, _ = Locale.objects.get_or_create(language_code="en")
        home.copy_for_translation(english)
        self.agenda.intro = "Texto editorial"
        self.agenda.save()
        call_command("setup_radioclub", stdout=StringIO())
        call_command("setup_radioclub", stdout=StringIO())
        self.agenda.refresh_from_db()
        self.assertEqual(self.agenda.intro, "Texto editorial")
        self.assertEqual(self.agenda.get_translations().count(), 1)
        self.assertEqual(EventIndexPage.objects.count(), 2)
