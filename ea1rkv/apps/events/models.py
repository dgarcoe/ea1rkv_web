"""Event models for EA1RKV radioclub activities and contests."""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index

from ea1rkv.apps.base.blocks import BODY_BLOCKS


class EventType(models.TextChoices):
    """Types of radioclub events."""

    CONTEST = "contest", _("Concurso")
    FIELD_DAY = "field_day", _("Actividad al aire libre")
    MEETING = "meeting", _("Reunión")
    WORKSHOP = "workshop", _("Taller")
    SOCIAL = "social", _("Encuentro social")
    OTHER = "other", _("Otra actividad")


class EventIndexPage(Page):
    """Listing page for all events."""

    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    max_count_per_parent = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["events.EventPage"]

    class Meta:
        verbose_name = "Agenda"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        show_past = request.GET.get("past", "").lower() == "true"
        events = EventPage.objects.child_of(self).live().public().annotate(
            effective_end=Coalesce("end_date", "start_date")
        )

        if show_past:
            events = events.filter(
                effective_end__lt=timezone.localdate()
            ).order_by("-start_date")
        else:
            events = events.filter(
                effective_end__gte=timezone.localdate()
            ).order_by("start_date", "start_time", "pk")

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
    content = RichTextField("Descripción", blank=True)
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
            heading="Fechas y horario (hora local de Vigo)",
        ),
        MultiFieldPanel(
            [
                FieldPanel("location"),
                FieldPanel("locator"),
            ],
            heading="Lugar",
        ),
        MultiFieldPanel(
            [
                FieldPanel("frequency"),
                FieldPanel("mode"),
            ],
            heading="Datos de radio",
        ),
        FieldPanel("header_image"),
        FieldPanel("intro"),
        FieldPanel("content"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.SearchField("content"),
        index.SearchField("location"),
    ]

    parent_page_types = ["events.EventIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Actividad"
        ordering = ["-start_date"]

    @property
    def is_past(self):
        return (self.end_date or self.start_date) < timezone.localdate()

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "La fecha final debe ser igual o posterior a la inicial."})
        if (self.start_time and self.end_time
                and (not self.end_date or self.end_date == self.start_date)
                and self.end_time <= self.start_time):
            raise ValidationError({"end_time": "La hora final debe ser posterior a la inicial; para actividades nocturnas indica la fecha final."})

    @property
    def is_multiday(self):
        return self.end_date is not None and self.end_date != self.start_date
