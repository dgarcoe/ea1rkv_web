from datetime import date
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image as PillowImage
from wagtail.images import get_image_model
from wagtail.documents import get_document_model
from wagtail.models import PageViewRestriction

from ea1rkv.apps.home.models import HomePage
from .models import CallsignMedia, CallsignsPage, ServicePage, ServicesPage, SpecialCallsignPage


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
            item.media_items.add(CallsignMedia(kind="image", image=image, title="Montaje <antena>", credit="Autor", group="Preparativos", sort_order=0))
            item.media_items.add(CallsignMedia(kind="image", image=image, title="Operación", group="En las ondas", sort_order=1))
            document = get_document_model().objects.create(title="Programa", file=SimpleUploadedFile("programa.txt", b"Programa"))
            item.media_items.add(CallsignMedia(kind="document", asset=document, title="Programa", description="<p>Programa de la actividad</p>"))
            revision = item.save_revision()
            self.assertNotContains(self.client.get(self.callsigns.url), item.title)
            revision.publish()
            response = self.client.get(item.url)
            self.assertContains(response, "Preparativos")
            self.assertContains(response, "En las ondas")
            self.assertContains(response, "Montaje &lt;antena&gt;")
            self.assertContains(response, image.file.url)
            self.assertContains(response, document.url)
            self.assertContains(self.client.get(self.callsigns.url), item.title)
            restored = revision.as_object()
            self.assertEqual(restored.media_items.count(), 3)
            item.layout = "report"
            item.save_revision().publish()
            html = self.client.get(item.url).content.decode()
            self.assertLess(html.index("Preparativos"), html.index("Información de la actividad."))
            PageViewRestriction.objects.create(page=item, restriction_type="login")
            self.assertNotContains(self.client.get(self.callsigns.url), item.title)

    def test_dates_and_rich_text_forms(self):
        item = SpecialCallsignPage(title="Prueba", callsign=" test ", start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            item.clean()
        item.end_date = date(2026, 2, 2)
        item.clean()
        self.assertEqual(item.callsign, "TEST")
        from ea1rkv.apps.base.editors import ClassicRichTextWidget
        for model in (ServicePage, SpecialCallsignPage):
            form = model.get_edit_handler().get_form_class()
            self.assertIsInstance(form.base_fields["content"].widget, ClassicRichTextWidget)
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

    def test_predefined_layouts_preserve_fields_and_change_order(self):
        item = self.callsigns.add_child(instance=SpecialCallsignPage(
            title="Plantillas", slug="plantillas", callsign="TEST", locale=self.home.locale,
            content="<p>Presentación conservada</p>", qsl_information="<p>Solicitud de prueba</p>",
            award_rules="<p>Bases de prueba</p>", bands="HF", modes="CW", location="Vigo",
        ))
        for layout, _ in SpecialCallsignPage.LAYOUTS:
            item.layout = layout
            item.save_revision().publish()
            response = self.client.get(item.url)
            for value in ("Presentación conservada", "Solicitud de prueba", "Bases de prueba", "HF", "CW", "Vigo"):
                self.assertContains(response, value)
            html = response.content.decode()
            if layout == "award":
                self.assertLess(html.index("Bases de prueba"), html.index("Presentación conservada"))
            else:
                self.assertLess(html.index("Presentación conservada"), html.index("Bases de prueba"))
