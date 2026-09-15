from datetime import date
from io import StringIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ClubDocument, ClubDocumentsPage, MemberDownloadEmail


@override_settings(CLUB_DOCUMENTS_PASSWORD="test-club-password")
class PrivateDocumentsTests(TestCase):
    def setUp(self):
        call_command("setup_radioclub", stdout=StringIO())
        self.page = ClubDocumentsPage.objects.get()
        self.page.intro = "<p>Introducción confidencial</p>"
        self.temp = TemporaryDirectory()
        self.storage = ClubDocument._meta.get_field("file").storage
        self.original_location = self.storage._location
        self.storage._location = self.temp.name
        self.storage.__dict__.pop("location", None)
        self.storage.__dict__.pop("base_location", None)
        self.doc = self.page.private_documents.create(
            title="Acta secreta",
            date=date.today(),
            file=SimpleUploadedFile("acta.pdf", b"private-pdf-content"),
        )
        self.page.save_revision().publish()
        self.url = reverse(
            "club_document_download", args=[self.page.pk, self.doc.download_key]
        )

    def tearDown(self):
        self.storage._location = self.original_location
        self.storage.__dict__.pop("location", None)
        self.storage.__dict__.pop("base_location", None)
        self.temp.cleanup()

    def login(self):
        return self.client.post(self.page.url, {"password": "test-club-password"})

    def test_gate_and_download(self):
        self.assertNotContains(self.client.get(self.page.url), "Acta secreta")
        self.assertNotContains(
            self.client.get(self.page.url), "Introducción confidencial"
        )
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.login().status_code, 302)
        response = self.client.get(self.page.url)
        self.assertContains(response, "Acta secreta")
        self.assertIn("no-store", response["Cache-Control"])
        response = self.client.get(self.url)
        self.assertContains(response, "Confirmo que soy socio del URV-Val Miñor")
        self.assertEqual(MemberDownloadEmail.objects.count(), 0)
        response = self.client.post(
            self.url,
            {"email": "SOCIO@example.com", "confirmed_member": "on"},
        )
        self.assertEqual(b"".join(response.streaming_content), b"private-pdf-content")
        self.assertIn("attachment", response["Content-Disposition"])
        contact = MemberDownloadEmail.objects.get()
        self.assertEqual(contact.email, "socio@example.com")
        self.assertEqual(contact.download_count, 1)
        self.assertEqual(contact.last_document, "Acta secreta")
        self.assertContains(self.client.get(self.url), 'value="socio@example.com"')
        self.client.post(
            self.url,
            {"email": "socio@example.com", "confirmed_member": "on"},
        )
        contact.refresh_from_db()
        self.assertEqual(contact.download_count, 2)
        with self.assertRaises(ValueError):
            str(self.doc.file.url)

    def test_email_and_membership_confirmation_are_required(self):
        self.login()
        self.client.post(self.url, {"email": "not-an-email", "confirmed_member": "on"})
        self.client.post(self.url, {"email": "socio@example.com"})
        self.assertEqual(MemberDownloadEmail.objects.count(), 0)

    def test_rotation_logout_and_drafts(self):
        self.login()
        with override_settings(CLUB_DOCUMENTS_PASSWORD="changed"):
            self.assertEqual(self.client.get(self.url).status_code, 302)
        draft = self.page.private_documents.create(
            title="Borrador secreto", date=date.today(), file="unpublished.pdf"
        )
        self.page.save_revision()
        self.assertNotContains(self.client.get(self.page.url), "Borrador secreto")
        self.assertEqual(
            self.client.get(
                reverse(
                    "club_document_download", args=[self.page.pk, draft.download_key]
                )
            ).status_code,
            404,
        )
        self.client.post(self.page.url, {"logout": "1"})
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_unconfigured_and_indexing(self):
        with override_settings(CLUB_DOCUMENTS_PASSWORD=""):
            self.login()
            self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertNotContains(self.client.get("/sitemap.xml"), "documentacion-socios")
        self.assertNotContains(self.client.get("/search/?query=Acta"), "Acta secreta")

    def test_csrf_and_unpublished_page(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(
            client.post(self.page.url, {"password": "test-club-password"}).status_code,
            403,
        )
        self.login()
        self.assertEqual(
            client.post(
                self.url,
                {"email": "socio@example.com", "confirmed_member": "on"},
            ).status_code,
            403,
        )
        self.page.unpublish()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_editor_renders_private_file_without_public_url(self):
        form = self.page.get_edit_handler().get_form_class()(instance=self.page)
        self.assertIn('type="file"', str(form.formsets["private_documents"]))
