"""Photo gallery models for EA1RKV website."""

from django.db import models

from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


class GalleryIndexPage(Page):
    """Listing page for all photo galleries."""

    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["gallery.GalleryPage"]

    class Meta:
        verbose_name = "Gallery Index"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["galleries"] = (
            GalleryPage.objects.child_of(self).live().order_by("-date")
        )
        return context


class GalleryPage(Page):
    """A photo gallery with multiple images."""

    date = models.DateField(help_text="Date of the event or activity")
    description = RichTextField(blank=True)
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Cover image shown in gallery listings",
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("description"),
        FieldPanel("cover_image"),
        InlinePanel("gallery_images", label="Gallery Images"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("description"),
    ]

    parent_page_types = ["gallery.GalleryIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Photo Gallery"
        ordering = ["-date"]


class GalleryImage(Orderable):
    """An individual image within a gallery."""

    page = ParentalKey(
        GalleryPage,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
    )
    caption = models.CharField(max_length=300, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Gallery Image"
