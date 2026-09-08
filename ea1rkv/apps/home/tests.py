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
            body=[("paragraph", "<p>Contenido del artículo.</p>")],
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
