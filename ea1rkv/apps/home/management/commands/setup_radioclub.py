"""Create the initial public pages without replacing editorial content."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.models import Locale, Page, Site

from ea1rkv.apps.base.models import RadioclubSettings
from ea1rkv.apps.blog.models import BlogIndexPage
from ea1rkv.apps.club.models import CallsignsPage, ServicesPage
from ea1rkv.apps.home.models import HomePage
from ea1rkv.apps.home.default_content import CLUB_DESCRIPTION


class Command(BaseCommand):
    help = "Prepara Inicio, Blog, Servicios e Indicativos especiales sin sobrescribir contenido."

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
                content=CLUB_DESCRIPTION,
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
        for model, title, slug, intro in (
            (ServicesPage, "Servicios", "servicios", "<p>Repetidores, frecuencias, equipos y otros recursos del radioclub. Consulta la ficha de cada recurso para conocer sus datos y condiciones de uso.</p>"),
            (CallsignsPage, "Indicativos especiales", "indicativos-especiales", "<p>Información, fechas y fotografías de las actividades con indicativos especiales del radioclub.</p>"),
        ):
            if not model.objects.child_of(home).exists():
                if home.get_children().filter(slug=slug).exists():
                    raise CommandError(f"Ya existe una página con slug {slug}. Revísala antes de crear la sección.")
                section = home.add_child(instance=model(
                    title=title, slug=slug, locale=home.locale,
                    intro=intro, show_in_menus=True,
                ))
                section.save_revision().publish()
        RadioclubSettings.objects.get_or_create(site=site)
        self.stdout.write(self.style.SUCCESS(
            "Inicio, Blog, Servicios e Indicativos especiales preparados. Edita los contenidos desde /admin/."
        ))
