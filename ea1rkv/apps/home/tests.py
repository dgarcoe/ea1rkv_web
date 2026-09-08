from io import StringIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image as PillowImage
from wagtail.images import get_image_model
from wagtail.models import PageViewRestriction, Site

from ea1rkv.apps.blog.models import BlogIndexPage, BlogPage
from ea1rkv.apps.home.models import HomePage


class RadioclubTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_radioclub", stdout=StringIO())
        cls.home = HomePage.objects.get()
        cls.blog = BlogIndexPage.objects.get()

    def post(self, title="Artículo de prueba", slug="prueba", live=True):
        post = self.blog.add_child(instance=BlogPage(
            title=title, slug=slug, intro="Experiencias de radioafición.",
            content="<p>Contenido del artículo.</p>",
            locale=self.home.locale, live=False,
        ))
        if live:
            post.save_revision().publish()
        return post

    def test_setup_is_repeatable_and_preserves_edits(self):
        self.home.about_title = "Texto editado por el club"
        self.home.save()
        call_command("setup_radioclub", stdout=StringIO())
        self.home.refresh_from_db()
        self.assertEqual(HomePage.objects.count(), 1)
        self.assertEqual(BlogIndexPage.objects.count(), 1)
        self.assertEqual(self.home.about_title, "Texto editado por el club")
        self.assertEqual(Site.objects.get(is_default_site=True).root_page_id, self.home.pk)

    def test_empty_home_blog_and_admin_are_reachable(self):
        home = self.client.get(self.home.url)
        self.assertContains(home, "Unión de Radioafeccionados de Vigo-Val Miñor")
        self.assertContains(home, "Visita el blog")
        self.assertNotContains(home, 'href="/events/"')
        self.assertContains(self.client.get(self.blog.url), "primeras noticias")
        self.assertEqual(self.client.get("/admin/", follow=True).status_code, 200)

    def test_publication_and_private_content(self):
        published = self.post()
        self.post(title="Borrador oculto", slug="borrador", live=False)
        private = self.post(title="Artículo privado", slug="privado")
        PageViewRestriction.objects.create(page=private, restriction_type="login")
        for url in [self.home.url, self.blog.url, "/feed/"]:
            response = self.client.get(url)
            self.assertContains(response, published.title)
            self.assertNotContains(response, "Borrador oculto")
            self.assertNotContains(response, "Artículo privado")
        self.assertContains(self.client.get(published.url), "Contenido del artículo.")
        self.assertContains(self.client.get(published.url), "Volver al blog")
        PageViewRestriction.objects.create(page=self.blog, restriction_type="login")
        self.assertNotContains(self.client.get(self.home.url), published.title)

    def test_pagination_preserves_encoded_tag(self):
        for i in range(10):
            post = self.post(slug=f"post-{i}")
            post.tags.add("radio & antenas")
            post.save_revision().publish()
        response = self.client.get(self.blog.url, {"tag": "radio & antenas"})
        self.assertEqual(len(response.context["posts"]), 9)
        self.assertContains(response, "tag=radio+%26+antenas&amp;page=2")
        response = self.client.get(self.blog.url, {"page": "2", "tag": "radio & antenas"})
        self.assertEqual(len(response.context["posts"]), 1)
        self.assertEqual(self.client.get(self.blog.url, {"page": "invalid"}).status_code, 200)

    def test_article_image_renders(self):
        from io import BytesIO
        data = BytesIO()
        PillowImage.new("RGB", (40, 40), "navy").save(data, format="PNG")
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            image = get_image_model().objects.create(
                title="Antena de prueba", file=SimpleUploadedFile("antena.png", data.getvalue(), content_type="image/png")
            )
            post = self.post()
            post.header_image = image
            post.save_revision().publish()
            self.assertContains(self.client.get(post.url), 'alt="Antena de prueba"')

    def test_editor_has_rich_text_without_block_fields(self):
        from wagtail.admin.rich_text import DraftailRichTextArea
        for model in (HomePage, BlogPage):
            form = model.get_edit_handler().get_form_class()
            self.assertIsInstance(form.base_fields["content"].widget, DraftailRichTextArea)
            self.assertNotIn("body", form.base_fields)
            self.assertNotIn("about_text", form.base_fields)

    def test_legacy_content_and_draft_conversion(self):
        from django.apps import apps
        from django.db import connection
        from ea1rkv.apps.base.migrations._richtext import migrate_content
        post = self.post(live=False)
        post.content = ""
        post.body = [("paragraph", "<p><b>Texto antiguo</b></p>"), ("heading", {"heading_text": "Antenas", "size": "h2"})]
        post.save()
        revision = post.save_revision()
        data = revision.content.copy()
        data.pop("content")
        revision.content = data
        revision.save(update_fields=["content"])
        from types import SimpleNamespace
        migrate_content(apps, SimpleNamespace(connection=connection), "blog", "BlogPage")
        post.refresh_from_db()
        revision.refresh_from_db()
        self.assertIn("<b>Texto antiguo</b>", post.content)
        self.assertIn("<h2>Antenas</h2>", post.content)
        self.assertEqual(len(post.body), 2)
        self.assertEqual(revision.content["content"], post.content)
        self.assertFalse(post.live)

    def test_header_photo_can_be_replaced_and_removed(self):
        from io import BytesIO
        data = BytesIO()
        PillowImage.new("RGB", (40, 40), "navy").save(data, format="PNG")
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            for name in ("vigo-uno", "vigo-dos"):
                image = get_image_model().objects.create(title=name, file=SimpleUploadedFile(name+".png", data.getvalue(), content_type="image/png"))
                self.home.hero_image = image
                self.home.hero_image_credit = "Foto de prueba · CC BY"
                self.home.save_revision().publish()
                response = self.client.get(self.home.url)
                self.assertContains(response, "club-hero-image")
                self.assertContains(response, "Foto de prueba · CC BY")
                self.assertContains(response, name)
            self.home.hero_image = None
            self.home.save_revision().publish()
            response = self.client.get(self.home.url)
            self.assertNotContains(response, "club-hero-image")
            self.assertNotContains(response, "Foto de prueba · CC BY")
