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
        default="Vigo Val Miñor Radioclub",
        help_text="Subtitle displayed below the hero heading",
    )
    hero_cta_text = models.CharField(
        max_length=50,
        blank=True,
        default="Learn More",
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
        help_text="Background image for the hero section",
    )

    # About section
    about_title = models.CharField(max_length=200, default="About Our Club")
    about_text = RichTextField(blank=True)

    # Flexible body content
    body = StreamField(BODY_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_subtitle"),
                FieldPanel("hero_cta_text"),
                FieldPanel("hero_cta_url"),
                FieldPanel("hero_image"),
            ],
            heading="Hero Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel("about_title"),
                FieldPanel("about_text"),
            ],
            heading="About Section",
        ),
        FieldPanel("body"),
    ]

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "blog.BlogIndexPage",
        "events.EventIndexPage",
        "gallery.GalleryIndexPage",
        "members.MemberIndexPage",
        "contact.ContactPage",
    ]

    class Meta:
        verbose_name = "Home Page"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["latest_posts"] = (
            self._get_latest_blog_posts()
        )
        context["upcoming_events"] = (
            self._get_upcoming_events()
        )
        return context

    def _get_latest_blog_posts(self, count=3):
        from ea1rkv.apps.blog.models import BlogPage

        return BlogPage.objects.live().order_by("-date")[:count]

    def _get_upcoming_events(self, count=3):
        from django.utils import timezone

        from ea1rkv.apps.events.models import EventPage

        return (
            EventPage.objects.live()
            .filter(start_date__gte=timezone.now().date())
            .order_by("start_date")[:count]
        )
