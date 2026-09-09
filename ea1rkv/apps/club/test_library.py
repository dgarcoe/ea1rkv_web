from importlib import import_module
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image as PillowImage
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.models import CollectionViewRestriction

from .models import CallsignDownload, CallsignMedia, CallsignPhoto, CallsignsPage, SpecialCallsignPage, youtube_video_id


class YouTubeURLTests(SimpleTestCase):
    def test_supported_video_urls(self):
        for url in (
            "https://www.youtube.com/watch?v=abcdefghijk&t=20s",
            "https://youtu.be/abcdefghijk?si=example",
            "https://youtube.com/shorts/abcdefghijk",
            "https://m.youtube.com/live/abcdefghijk",
            "https://www.youtube-nocookie.com/embed/abcdefghijk",
        ):
            self.assertEqual(youtube_video_id(url), "abcdefghijk")

    def test_invalid_urls_never_become_embeds(self):
        for url in (
            "javascript:alert(1)", "https://youtube.com.evil.example/watch?v=abcdefghijk",
            "https://youtube.com@evil.example/watch?v=abcdefghijk", "https://youtube.com/playlist?list=abcdefghijk",
            "https://youtu.be/too-short", "https://youtube.com:invalid/watch?v=abcdefghijk", "https://[",
        ):
            self.assertEqual(youtube_video_id(url), "")
            self.assertEqual(CallsignMedia(youtube_url=url).youtube_embed_url, "")


class MediaLibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_radioclub", stdout=StringIO())
        cls.index = CallsignsPage.objects.get()
        cls.page = cls.index.add_child(instance=SpecialCallsignPage(
            title="Actividad de prueba", slug="biblioteca-prueba", callsign="TEST",
            locale=cls.index.locale, live=False,
        ))

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

    def asset(self, name):
        return get_document_model().objects.create(title=name, file=SimpleUploadedFile(name, b"Test media"))

    def photo(self):
        data = BytesIO()
        PillowImage.new("RGB", (40, 40), "navy").save(data, format="PNG")
        return get_image_model().objects.create(title="Antena", file=SimpleUploadedFile("antena.png", data.getvalue()))

    def fill_library(self):
        self.page.media_items.add(
            CallsignMedia(kind="image", title="Fotografía única", description="<p>Descripción de la imagen</p>", image=self.photo(), group="Montaje", sort_order=0),
            CallsignMedia(kind="document", title="Bases únicas", description="<p>Descripción del documento</p>", asset=self.asset("bases.pdf"), sort_order=1),
            CallsignMedia(kind="video", title="Vídeo único", description="<p>Descripción del vídeo</p>", asset=self.asset("video.mp4"), group="Operación", sort_order=2),
            CallsignMedia(kind="audio", title="Audio único", description="<p>Descripción del audio</p>", asset=self.asset("audio.mp3"), group="Operación", sort_order=3),
            CallsignMedia(kind="youtube", title="YouTube único", description="<p>Descripción de YouTube</p>", youtube_url="https://youtu.be/abcdefghijk", sort_order=4),
        )
        self.page.save_revision().publish()

    def test_all_types_have_visible_descriptions_and_correct_players(self):
        self.fill_library()
        response = self.client.get(self.page.url)
        for description in ("imagen", "documento", "vídeo", "audio"):
            self.assertContains(response, "Descripción d" + ("e la " if description == "imagen" else "el ") + description)
        self.assertContains(response, "Descripción de YouTube")
        self.assertContains(response, "<video controls")
        self.assertContains(response, "<audio controls")
        self.assertContains(response, "https://www.youtube-nocookie.com/embed/abcdefghijk")
        self.assertNotContains(response, "autoplay")
        self.assertEqual(response.context["library_count"], 5)

    def test_each_type_filter_and_combined_group_filter(self):
        self.fill_library()
        for kind, _ in CallsignMedia.TYPES:
            response = self.client.get(self.page.url, {"tipo": kind})
            self.assertEqual(response.context["library_count"], 1)
            self.assertEqual(response.context["library_entries"][0].kind, kind)
        response = self.client.get(self.page.url, {"tipo": "audio", "grupo": "Operación"})
        self.assertContains(response, "Descripción del audio")
        self.assertNotContains(response, "Descripción del vídeo")
        response = self.client.get(self.page.url, {"tipo": "audio", "grupo": "Montaje"})
        self.assertContains(response, "No hay contenido con estos filtros")
        self.assertEqual(self.client.get(self.page.url, {"tipo": "invalid"}).context["library_count"], 5)

    def test_pagination_keeps_type_and_escaped_group(self):
        for number in range(13):
            self.page.media_items.add(CallsignMedia(kind="youtube", title=f"Vídeo {number}", group="Radio & antenas", youtube_url="https://youtu.be/abcdefghijk", sort_order=number))
        self.page.save_revision().publish()
        response = self.client.get(self.page.url, {"tipo": "youtube", "grupo": "Radio & antenas"})
        self.assertEqual(len(response.context["library_entries"]), 12)
        self.assertContains(response, "tipo=youtube&amp;grupo=Radio+%26+antenas&amp;biblioteca_pagina=2#biblioteca")
        response = self.client.get(self.page.url, {"tipo": "youtube", "grupo": "Radio & antenas", "biblioteca_pagina": 2})
        self.assertEqual(len(response.context["library_entries"]), 1)

    def test_draft_media_only_appears_after_publication(self):
        self.page.save_revision().publish()
        self.page.media_items.add(CallsignMedia(kind="youtube", title="Material en borrador", youtube_url="https://youtu.be/abcdefghijk"))
        revision = self.page.save_revision()
        self.assertNotContains(self.client.get(self.page.url), "Material en borrador")
        self.assertEqual(revision.as_object().media_items.count(), 1)
        revision.publish()
        self.assertContains(self.client.get(self.page.url), "Material en borrador")

    def test_content_validation_matches_type(self):
        for kind, _ in CallsignMedia.TYPES:
            with self.assertRaises(ValidationError):
                CallsignMedia(kind=kind, title="Sin contenido").clean()
        document = self.asset("texto.pdf")
        for kind in ("audio", "video"):
            with self.assertRaises(ValidationError):
                CallsignMedia(kind=kind, title="Formato erróneo", asset=document).clean()
        with self.assertRaises(ValidationError):
            CallsignMedia(kind="youtube", title="Dos fuentes", asset=document, youtube_url="https://youtu.be/abcdefghijk").clean()
        CallsignMedia(kind="video", title="Vídeo", asset=self.asset("prueba.mp4")).clean()

    def test_media_serving_mime_types_and_collection_permissions(self):
        for filename, content_type in (("video.mp4", "video/mp4"), ("audio.mp3", "audio/mpeg")):
            document = self.asset(filename)
            response = self.client.get(document.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], content_type)
            self.assertNotIn("attachment", response.get("Content-Disposition", ""))
            response.close()
        CollectionViewRestriction.objects.create(collection=document.collection, restriction_type="login")
        response = self.client.get(document.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_has_one_library_and_classic_description_editor(self):
        user = get_user_model().objects.create_superuser("library-editor", "editor@example.com", "test-password")
        self.client.force_login(user)
        response = self.client.get(f"/admin/pages/{self.page.pk}/edit/")
        self.assertContains(response, "Biblioteca del indicativo")
        form_class = SpecialCallsignPage.get_edit_handler().get_form_class()
        self.assertIn("media_items", form_class.formsets)
        self.assertNotIn("photos", form_class.formsets)
        self.assertNotIn("downloads", form_class.formsets)

    def test_migration_keeps_published_items_and_distinct_old_draft(self):
        image = self.photo()
        document = self.asset("bases.pdf")
        self.page.photos.add(CallsignPhoto(image=image, caption="Foto <original>", credit="Autor", group="Montaje"))
        self.page.downloads.add(CallsignDownload(document=document, description="Bases originales"))
        revision = self.page.save_revision()
        # Simulate a revision saved before the new relation existed.
        data = revision.content.copy()
        data.pop("media_items", None)
        data["photos"][0]["caption"] = "Foto del borrador"
        revision.content = data
        revision.save(update_fields=["content"])
        # Save the original live child relations without publishing that draft.
        self.page.save()
        migrate = import_module("ea1rkv.apps.club.migrations.0004_populate_media_library").populate_library
        editor = SimpleNamespace(connection=connection)
        migrate(apps, editor)
        migrate(apps, editor)
        self.assertEqual(CallsignMedia.objects.filter(page=self.page).count(), 2)
        migrated = CallsignMedia.objects.get(page=self.page, kind="image")
        self.assertEqual(migrated.description, "<p>Foto &lt;original&gt;</p>")
        self.assertEqual(migrated.credit, "Autor")
        revision.refresh_from_db()
        draft = revision.as_object()
        self.assertEqual(draft.media_items.count(), 2)
        self.assertEqual(draft.media_items.all()[0].description, "<p>Foto del borrador</p>")
        revision.publish()
        self.assertContains(self.client.get(self.page.url), "Foto del borrador")
