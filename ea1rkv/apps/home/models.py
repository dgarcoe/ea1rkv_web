"""Home page models for EA1RKV website."""

from django.db import models

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from ea1rkv.apps.base.blocks import BODY_BLOCKS


class HomePage(Page):
    """The main landing page for the radioclub website."""

    # Hero section
    hero_title = models.CharField(
        max_length=200,
        default="EA1RKV",
        help_text="Main heading displayed in the hero section",
    )
    hero_subtitle = models.CharField(
        max_length=300,
        default="Unión de Radioafeccionados de Vigo-Val Miñor",
        help_text="Subtitle displayed below the hero heading",
    )
    hero_cta_text = models.CharField(
        max_length=50,
        blank=True,
        default="Conoce el radioclub",
        help_text="Call-to-action button text",
    )
    hero_cta_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Call-to-action button URL",
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Imagen de cabecera",
        help_text="Sube la fotografía de Vigo que quieras mostrar. Puedes cambiarla en cualquier momento.",
    )

    hero_image_credit = models.CharField("Créditos de la imagen", max_length=300, blank=True, help_text="Autor, fuente y licencia, si corresponde.")

    # About section
    about_title = models.CharField(max_length=200, default="Nuestro radioclub")
    about_text = RichTextField(blank=True)

    # Flexible body content
    body = StreamField(BODY_BLOCKS, blank=True, use_json_field=True)

    # Legacy fields remain stored for recovery, but are not exposed in the editor.
    content = RichTextField(
        "Contenido", blank=True,
        features=["h2", "h3", "bold", "italic", "ol", "ul", "link", "document-link", "image", "embed"],
        help_text="Escribe y da formato al texto; puedes insertar imágenes y enlaces desde la barra de herramientas.",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_subtitle"),
                FieldPanel("hero_cta_text"),
                FieldPanel("hero_cta_url"),
                FieldPanel("hero_image"),
                FieldPanel("hero_image_credit"),
            ],
            heading="Cabecera",
        ),
        MultiFieldPanel(
            [
                FieldPanel("about_title"),
                FieldPanel("content"),
            ],
            heading="Presentación del radioclub",
        ),
    ]

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "club.ServicesPage",
        "club.CallsignsPage",
        "blog.BlogIndexPage",
        "events.EventIndexPage",
        "gallery.GalleryIndexPage",
        "members.MemberIndexPage",
        "contact.ContactPage",
    ]

    class Meta:
        verbose_name = "Home Page"

    def get_context(self, request, *args, **kwargs):
        from ea1rkv.apps.blog.models import BlogIndexPage, BlogPage

        context = super().get_context(request, *args, **kwargs)
        from ea1rkv.apps.club.models import CallsignsPage, ServicesPage
        context["services_index"] = ServicesPage.objects.child_of(self).live().public().first()
        context["callsigns_index"] = CallsignsPage.objects.child_of(self).live().public().first()
        blog = BlogIndexPage.objects.child_of(self).live().public().first()
        context["blog_index"] = blog
        context["latest_posts"] = (
            BlogPage.objects.child_of(blog).live().public()
            .select_related("header_image").order_by("-date", "-pk")[:3]
            if blog else BlogPage.objects.none()
        )
        return context
