"""Blog models for EA1RKV website news and articles."""

from django.db import models
from django.utils import timezone

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from ea1rkv.apps.base.blocks import BODY_BLOCKS


@register_snippet
class BlogCategory(models.Model):
    """Blog post category (e.g., Contests, Technical, Club News)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
    ]

    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogPageTag(TaggedItemBase):
    """Through model for blog post tags."""

    content_object = ParentalKey(
        "blog.BlogPage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


class BlogIndexPage(Page):
    """Listing page for all blog posts."""

    intro = models.TextField(blank=True, help_text="Introduction text for the blog")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BlogPage"]

    class Meta:
        verbose_name = "Blog Index"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        posts = BlogPage.objects.child_of(self).live().order_by("-date")

        # Filter by category
        category_slug = request.GET.get("category")
        if category_slug:
            posts = posts.filter(categories__slug=category_slug)

        # Filter by tag
        tag = request.GET.get("tag")
        if tag:
            posts = posts.filter(tags__name=tag)

        context["posts"] = posts
        context["categories"] = BlogCategory.objects.all()
        return context


class BlogPage(Page):
    """Individual blog post."""

    date = models.DateField(default=timezone.now, help_text="Post publication date")
    intro = models.TextField(
        max_length=500,
        help_text="Brief summary shown in listings",
    )
    body = StreamField(BODY_BLOCKS, use_json_field=True)
    header_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    categories = ParentalManyToManyField("blog.BlogCategory", blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    author_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Author name or callsign",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("author_name"),
            ],
            heading="Post Metadata",
        ),
        FieldPanel("header_image"),
        FieldPanel("intro"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("categories"),
                FieldPanel("tags"),
            ],
            heading="Classification",
        ),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.SearchField("author_name"),
    ]

    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Blog Post"
        ordering = ["-date"]
