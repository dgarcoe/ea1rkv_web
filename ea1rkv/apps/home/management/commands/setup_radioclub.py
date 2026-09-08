"""Create the initial public pages without replacing editorial content."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.models import Locale, Page, Site

from ea1rkv.apps.base.models import RadioclubSettings
from ea1rkv.apps.blog.models import BlogIndexPage
from ea1rkv.apps.home.models import HomePage


class Command(BaseCommand):
    help = "Crea Inicio y Blog para EA1RKV sin sobrescribir páginas existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            raise CommandError("Configura primero un sitio predeterminado en Wagtail.")
        home = HomePage.objects.filter(pk=site.root_page_id).first()
        if home is None:
            starter = site.root_page
            if (starter.specific_class is not Page or starter.slug != "home"
                    or starter.get_children().exists() or HomePage.objects.exists()):
                raise CommandError(
                    "El sitio ya tiene contenido. Selecciona su HomePage como raíz "
                    "en Ajustes > Sitios y vuelve a ejecutar este comando."
                )
            locale, _ = Locale.objects.get_or_create(language_code="es")
            root = Page.get_first_root_node()
            slug = "inicio"
            if root.get_children().filter(slug=slug).exists():
                raise CommandError("Ya existe una página con slug inicio; revísala en Wagtail.")
            home = root.add_child(instance=HomePage(
                title="Inicio", slug=slug, locale=locale,
                hero_title="EA1RKV",
                hero_subtitle="Unión de Radioafeccionados de Vigo-Val Miñor",
                about_title="La radio nos reúne",
                content=(
                    "<p>Somos la Unión de Radioafeccionados de Vigo-Val Miñor, "
                    "con indicativo EA1RKV. Un punto de encuentro para quienes "
                    "compartimos el interés por la radioafición.</p>"
                    "<p>En esta web podrás conocer el radioclub y seguir nuestro blog: "
                    "noticias, experiencias y artículos sobre radio.</p>"
                ),
                search_description="Conoce EA1RKV, la Unión de Radioafeccionados de Vigo-Val Miñor, y sigue nuestro blog de radioafición.",
            ))
            home.save_revision().publish()
            site.root_page = home
            site.site_name = "EA1RKV · Vigo-Val Miñor"
            site.save()
        blog = BlogIndexPage.objects.child_of(home).first()
        if blog is None:
            if home.get_children().filter(slug="blog").exists() or BlogIndexPage.objects.exists():
                raise CommandError("Ya existe otro blog o una página con slug blog. Revísala en Wagtail.")
            blog = home.add_child(instance=BlogIndexPage(
                title="Blog", slug="blog", locale=home.locale, show_in_menus=True,
                intro="Noticias del radioclub, experiencias en las ondas y artículos de radioafición.",
                search_description="Noticias y artículos de radioafición de EA1RKV.",
            ))
            blog.save_revision().publish()
        RadioclubSettings.objects.get_or_create(site=site)
        self.stdout.write(self.style.SUCCESS(
            "Inicio y Blog preparados. Edita los contenidos desde /admin/."
        ))
