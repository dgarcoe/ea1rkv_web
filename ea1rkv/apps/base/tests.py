from io import BytesIO, StringIO
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.contrib.staticfiles import finders
from django.test import TestCase, SimpleTestCase, override_settings
from PIL import Image as PillowImage
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.rich_text import expand_db_html

from ea1rkv.apps.home.models import HomePage
from .editors import ClassicRichTextWidget, database_html, editor_html


class ClassicHTMLTests(SimpleTestCase):
    def test_formatting_and_tables_survive(self):
        html = '<h2>Título</h2><p><strong>Radio</strong> <u>Vigo</u></p><table><tbody><tr><td>HF</td></tr></tbody></table>'
        self.assertEqual(database_html(editor_html(html)), html)

    def test_unsafe_html_is_removed(self):
        value = database_html('<p onclick="alert(1)">Texto</p><script>alert(2)</script><a href="javascript:alert(3)">Enlace</a><iframe src="https://example.com"></iframe>')
        for unsafe in ('onclick', '<script', 'javascript:', '<iframe'):
            self.assertNotIn(unsafe, value)
        self.assertIn('Texto', value)

    def test_existing_media_reference_survives_without_fetching(self):
        value = '<embed embedtype="media" url="https://www.youtube.com/watch?v=abcdefghijk">'
        restored = BeautifulSoup(database_html(editor_html(value)), 'html.parser').embed
        self.assertEqual(restored['embedtype'], 'media')
        self.assertEqual(restored['url'], 'https://www.youtube.com/watch?v=abcdefghijk')


class ClassicEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('setup_radioclub', stdout=StringIO())
        cls.home = HomePage.objects.get()
        cls.user = get_user_model().objects.create_superuser('editor', 'editor@example.com', 'test-password')

    def test_authenticated_admin_uses_classic_editor_and_local_assets(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/admin/pages/{self.home.pk}/edit/')
        self.assertContains(response, 'ea1rkv-classic-editor')
        self.assertContains(response, 'tinymce/tinymce.min.js')
        self.assertContains(response, 'js/classic-editor.js')
        for path in ClassicRichTextWidget.Media.js + ['tinymce/langs/es.js']:
            self.assertTrue(finders.find(path), path)

    def test_links_images_and_revision_round_trip(self):
        image_data = BytesIO()
        PillowImage.new('RGB', (40, 40), 'navy').save(image_data, format='PNG')
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            image = get_image_model().objects.create(title='Antena', file=SimpleUploadedFile('antena.png', image_data.getvalue()))
            doc = get_document_model().objects.create(title='Bases', file=SimpleUploadedFile('bases.txt', b'Bases'))
            original = f'<p><a linktype="page" id="{self.home.pk}">Inicio</a> <a linktype="document" id="{doc.pk}">Bases</a></p><embed embedtype="image" id="{image.pk}" format="fullwidth" alt="Antena &quot;Vigo&quot; &amp; radio">'
            widget = ClassicRichTextWidget()
            result = widget.value_from_datadict({'content': editor_html(original)}, {}, 'content')
            self.assertEqual(BeautifulSoup(result, 'html.parser').embed['alt'], 'Antena "Vigo" & radio', editor_html(original) + '\n' + result)
            self.home.content = result
            restored = self.home.save_revision().as_object()
            output = expand_db_html(restored.content)
            self.assertIn(self.home.url, output)
            self.assertIn(doc.url, output)
            self.assertIn('<img', output)
            self.assertEqual(database_html(editor_html(result)), result)
            self.assertNotIn('data-wagtail', result)
