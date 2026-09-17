from django.test import RequestFactory, TestCase
from wagtail.models import Locale, Page, PageViewRestriction, Site

from .templatetags.navigation_tags import main_menu


class SharedMenuOrderTests(TestCase):
    def setUp(self):
        es, _ = Locale.objects.get_or_create(language_code="es")
        en, _ = Locale.objects.get_or_create(language_code="en")
        root = Page.get_first_root_node()
        self.source = root.add_child(instance=Page(
            title="Principal", slug="menu-source", locale=es,
        ))
        self.translated = root.add_child(instance=Page(
            title="English", slug="menu-english", locale=en,
            translation_key=self.source.translation_key,
        ))
        Site.objects.create(
            hostname="menu.example.com", root_page=self.source, port=80,
        )
        self.request = RequestFactory().get("/", HTTP_HOST="menu.example.com")
        self.sources = {}
        self.translations = {}
        for name in ("Blog", "Servicios", "Indicativos"):
            self.sources[name] = self.source.add_child(instance=Page(
                title=name, slug=name.lower(), locale=es, show_in_menus=True,
            ))
        for name in ("Indicativos", "Blog", "Servicios"):
            self.translations[name] = self.translated.add_child(instance=Page(
                title=name + " EN", slug=name.lower(), locale=en,
                translation_key=self.sources[name].translation_key,
                show_in_menus=True,
            ))

    def menu(self):
        return main_menu(
            {"request": self.request}, parent=self.translated,
            calling_page=self.translations["Blog"],
        )["menuitems"]

    def test_translated_tree_follows_source_order_and_keeps_active_link(self):
        items = self.menu()
        self.assertEqual([p.pk for p in items], [
            self.translations[name].pk
            for name in ("Blog", "Servicios", "Indicativos")
        ])
        self.assertTrue(items[0].active)
        self.assertFalse(items[1].active)

    def test_source_reordering_updates_translated_menu(self):
        self.sources["Indicativos"].move(self.sources["Blog"], pos="left")
        self.assertEqual([p.pk for p in self.menu()], [
            self.translations[name].pk
            for name in ("Indicativos", "Blog", "Servicios")
        ])

    def test_draft_and_restricted_translations_stay_hidden(self):
        page = self.translations["Servicios"]
        page.live = False
        page.save()
        PageViewRestriction.objects.create(
            page=self.translations["Indicativos"], restriction_type="login",
        )
        self.assertEqual([p.pk for p in self.menu()], [
            self.translations["Blog"].pk,
        ])
