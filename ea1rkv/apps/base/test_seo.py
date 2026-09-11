from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from wagtail.models import Locale, Page, Site

from ea1rkv.apps.home.models import HomePage


class SeoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_radioclub", stdout=StringIO())
        cls.home = HomePage.objects.get()
        site = Site.objects.get(is_default_site=True)
        site.hostname = "ea1rkv.com"
        site.port = 443
        site.save()

    def test_home_has_descriptive_metadata_and_structured_data(self):
        response = self.client.get(self.home.url, secure=True, HTTP_HOST="ea1rkv.com")
        self.assertContains(response, "Radioafición y radioclub en Vigo y Val Miñor")
        self.assertContains(
            response, '<link rel="canonical" href="https://ea1rkv.com/">', html=True
        )
        self.assertContains(response, 'type="application/ld+json"')
        self.assertContains(response, '"@type":"Organization"')
        self.assertContains(response, '"@type":"WebSite"')

    @override_settings(GOOGLE_SITE_VERIFICATION="verification-token")
    def test_search_console_token_is_optional_and_safe(self):
        response = self.client.get(self.home.url, secure=True, HTTP_HOST="ea1rkv.com")
        self.assertContains(
            response, 'name="google-site-verification" content="verification-token"'
        )

    def test_query_pages_are_not_indexed_and_canonical_drops_query(self):
        response = self.client.get(
            self.home.url + "?preview=1", secure=True, HTTP_HOST="ea1rkv.com"
        )
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertNotContains(response, "preview=1")

    def test_robots_points_to_real_sitemap(self):
        response = self.client.get("/robots.txt", secure=True, HTTP_HOST="ea1rkv.com")
        self.assertContains(response, "Sitemap: https://ea1rkv.com/sitemap.xml")
        sitemap = self.client.get("/sitemap.xml", secure=True, HTTP_HOST="ea1rkv.com")
        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, "https://ea1rkv.com/")

    def test_sitemap_and_head_include_published_translation(self):
        english, _ = Locale.objects.get_or_create(language_code="en")
        translated = Page.get_first_root_node().add_child(
            instance=HomePage(
                title="Home",
                slug="home-en",
                locale=english,
                translation_key=self.home.translation_key,
            )
        )
        translated.save_revision().publish()
        home = self.client.get(self.home.url, secure=True, HTTP_HOST="ea1rkv.com")
        self.assertContains(home, 'hreflang="en"')
        sitemap = self.client.get("/sitemap.xml", secure=True, HTTP_HOST="ea1rkv.com")
        self.assertContains(sitemap, "https://ea1rkv.com/en/")

    @override_settings(WAGTAIL_SITE_HOSTNAME="ea1rkv.com", WAGTAIL_SITE_PORT="443")
    def test_setup_can_configure_production_site_hostname(self):
        call_command("setup_radioclub", stdout=StringIO())
        site = Site.objects.get(is_default_site=True)
        self.assertEqual((site.hostname, site.port), ("ea1rkv.com", 443))
