"""Event models for EA1RKV radioclub activities and contests."""

from django.db import models
from django.utils import timezone

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from ea1rkv.apps.base.blocks import BODY_BLOCKS


class EventType(models.TextChoices):
    """Types of radioclub events."""

    CONTEST = "contest", "Contest"
    FIELD_DAY = "field_day", "Field Day"
    MEETING = "meeting", "Meeting"
    WORKSHOP = "workshop", "Workshop"
    SOCIAL = "social", "Social Event"
    OTHER = "other", "Other"


class EventIndexPage(Page):
    """Listing page for all events."""

    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["events.EventPage"]

    class Meta:
        verbose_name = "Events Index"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        show_past = request.GET.get("past", "").lower() == "true"
        events = EventPage.objects.child_of(self).live()

        if show_past:
            events = events.filter(
                start_date__lt=timezone.now().date()
            ).order_by("-start_date")
        else:
            events = events.filter(
                start_date__gte=timezone.now().date()
            ).order_by("start_date")

        # Filter by event type
        event_type = request.GET.get("type")
        if event_type and event_type in EventType.values:
            events = events.filter(event_type=event_type)

        context["events"] = events
        context["show_past"] = show_past
        context["event_types"] = EventType.choices
        return context


class EventPage(Page):
    """Individual event page."""

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER,
    )
    start_date = models.DateField(help_text="Event start date")
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Event end date (leave blank for single-day events)",
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=300, blank=True)
    locator = models.CharField(
        max_length=10,
        blank=True,
        help_text="Maidenhead grid locator for the event location",
    )
    frequency = models.CharField(
        max_length=100,
        blank=True,
        help_text="Operating frequencies (e.g., 7.090 MHz, 144.300 MHz)",
    )
    mode = models.CharField(
        max_length=100,
        blank=True,
        help_text="Operating modes (e.g., SSB, CW, FT8)",
    )
    intro = models.TextField(
        max_length=500,
        help_text="Brief event description for listings",
    )
    body = StreamField(BODY_BLOCKS, use_json_field=True, blank=True)
    header_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("event_type"),
        MultiFieldPanel(
            [
                FieldPanel("start_date"),
                FieldPanel("end_date"),
                FieldPanel("start_time"),
                FieldPanel("end_time"),
            ],
            heading="Date & Time",
        ),
        MultiFieldPanel(
            [
                FieldPanel("location"),
                FieldPanel("locator"),
            ],
            heading="Location",
        ),
        MultiFieldPanel(
            [
                FieldPanel("frequency"),
                FieldPanel("mode"),
            ],
            heading="Radio Details",
        ),
        FieldPanel("header_image"),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.SearchField("location"),
    ]

    parent_page_types = ["events.EventIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Event"
        ordering = ["-start_date"]

    @property
    def is_past(self):
        return self.start_date < timezone.now().date()

    @property
    def is_multiday(self):
        return self.end_date is not None and self.end_date != self.start_date
