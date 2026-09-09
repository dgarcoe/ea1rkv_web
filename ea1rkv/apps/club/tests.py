from datetime import date
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image as PillowImage
from wagtail.images import get_image_model
from wagtail.models import PageViewRestriction

from ea1rkv.apps.home.models import HomePage
from .models import CallsignPhoto, CallsignsPage, ServicePage, ServicesPage, SpecialCallsignPage


class ClubSectionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_radioclub", stdout=StringIO())
        cls.home = HomePage.objects.get()
        cls.services = ServicesPage.objects.get()
        cls.callsigns = CallsignsPage.objects.get()

    def test_setup_navigation_and_empty_sections(self):
        self.services.intro = "<p>Presentación editada</p>"
        self.services.save()
        call_command("setup_radioclub", stdout=StringIO())
        self.services.refresh_from_db()
        self.assertEqual(ServicesPage.objects.count(), 1)
        self.assertEqual(CallsignsPage.objects.count(), 1)
        self.assertEqual(self.services.intro, "<p>Presentación editada</p>")
        self.assertContains(self.client.get(self.home.url), self.services.url)
        self.assertContains(self.client.get(self.home.url), self.callsigns.url)
        self.assertContains(self.client.get(self.services.url), "Próximamente")
        self.assertContains(self.client.get(self.callsigns.url), "Próximamente")

    def test_service_details_and_visibility(self):
        item = self.services.add_child(instance=ServicePage(
            title="Recurso de prueba", slug="recurso", kind="repeater",
            frequency="145.000", input_frequency="144.400", mode="FM",
            access="Configuración de prueba", content="<p>Descripción técnica.</p>",
            locale=self.home.locale, live=False,
        ))
        self.assertNotContains(self.client.get(self.services.url), item.title)
        item.save_revision().publish()
        self.assertContains(self.client.get(self.services.url), item.title)
        response = self.client.get(item.url)
        self.assertContains(response, "144.400")
        self.assertContains(response, "Descripción técnica.")
        PageViewRestriction.objects.create(page=item, restriction_type="login")
        self.assertNotContains(self.client.get(self.services.url), item.title)
        PageViewRestriction.objects.create(page=self.services, restriction_type="login")
        self.assertNotContains(self.client.get(self.home.url), self.services.url)

    def test_callsign_photo_revision_and_rendering(self):
        data = BytesIO()
        PillowImage.new("RGB", (80, 60), "navy").save(data, format="PNG")
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            image = get_image_model().objects.create(title="Foto de prueba", file=SimpleUploadedFile("prueba.png", data.getvalue(), content_type="image/png"))
            item = self.callsigns.add_child(instance=SpecialCallsignPage(
                title="Actividad de prueba", slug="actividad", callsign="TEST",
                content="<p>Información de la actividad.</p>", start_date=date(2026, 1, 1),
                cover_image=image, locale=self.home.locale, live=False,
            ))
            item.photos.add(CallsignPhoto(image=image, caption="Montaje <antena>", credit="Autor", group="Preparativos", sort_order=0))
            item.photos.add(CallsignPhoto(image=image, caption="Operación", group="En las ondas", sort_order=1))
            revision = item.save_revision()
            self.assertNotContains(self.client.get(self.callsigns.url), item.title)
            revision.publish()
            response = self.client.get(item.url)
            self.assertContains(response, "Preparativos")
            self.assertContains(response, "En las ondas")
            self.assertContains(response, "Montaje &lt;antena&gt;")
            self.assertContains(response, image.file.url)
            self.assertContains(self.client.get(self.callsigns.url), item.title)
            restored = revision.as_object()
            self.assertEqual(restored.photos.count(), 2)
            PageViewRestriction.objects.create(page=item, restriction_type="login")
            self.assertNotContains(self.client.get(self.callsigns.url), item.title)

    def test_dates_and_rich_text_forms(self):
        item = SpecialCallsignPage(title="Prueba", callsign=" test ", start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            item.clean()
        item.end_date = date(2026, 2, 2)
        item.clean()
        self.assertEqual(item.callsign, "TEST")
        from wagtail.admin.rich_text import DraftailRichTextArea
        for model in (ServicePage, SpecialCallsignPage):
            form = model.get_edit_handler().get_form_class()
            self.assertIsInstance(form.base_fields["content"].widget, DraftailRichTextArea)
            self.assertNotIn("body", form.base_fields)

    def test_callsigns_pagination(self):
        for number in range(13):
            item = self.callsigns.add_child(instance=SpecialCallsignPage(
                title=f"Actividad {number}", slug=f"actividad-{number}", callsign=f"TEST{number}", locale=self.home.locale,
            ))
            item.save_revision().publish()
        self.assertEqual(len(self.client.get(self.callsigns.url).context["callsigns"]), 12)
        self.assertEqual(len(self.client.get(self.callsigns.url, {"page": 2}).context["callsigns"]), 1)
        self.assertEqual(self.client.get(self.callsigns.url, {"page": "invalid"}).status_code, 200)
