"""Contact page model using Wagtail's built-in form builder."""

from django.db import models

from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import RichTextField

from modelcluster.fields import ParentalKey


class ContactFormField(AbstractFormField):
    """Dynamic form fields for the contact page."""

    page = ParentalKey(
        "contact.ContactPage",
        on_delete=models.CASCADE,
        related_name="form_fields",
    )


class ContactPage(AbstractEmailForm):
    """Contact page with a configurable form builder."""

    intro = RichTextField(blank=True, help_text="Text displayed above the form")
    thank_you_text = RichTextField(
        blank=True,
        help_text="Text displayed after successful form submission",
    )
    map_embed_url = models.URLField(
        blank=True,
        help_text="Google Maps or OpenStreetMap embed URL for club location",
    )

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Form Fields"),
        FieldPanel("thank_you_text"),
        FieldPanel("map_embed_url"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("from_address", classname="col6"),
                        FieldPanel("to_address", classname="col6"),
                    ]
                ),
                FieldPanel("subject"),
            ],
            heading="Email Settings",
        ),
    ]

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Contact Page"
