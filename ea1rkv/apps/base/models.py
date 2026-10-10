"""Base models and site settings for EA1RKV website."""

from django.db import models

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


@register_setting
class SocialMediaSettings(BaseSiteSetting):
    """Social media links displayed across the site."""

    facebook = models.URLField(blank=True, help_text="Facebook page URL")
    twitter = models.URLField(blank=True, help_text="Twitter/X profile URL")
    instagram = models.URLField(blank=True, help_text="Instagram profile URL")
    youtube = models.URLField(blank=True, help_text="YouTube channel URL")
    qrz = models.URLField(blank=True, help_text="QRZ.com profile URL")

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("facebook"),
                FieldPanel("twitter"),
                FieldPanel("instagram"),
                FieldPanel("youtube"),
                FieldPanel("qrz"),
            ],
            heading="Social Media Links",
        ),
    ]

    class Meta:
        verbose_name = "Social Media Settings"


@register_setting
class RadioclubSettings(BaseSiteSetting):
    """General radioclub information."""

    callsign = models.CharField(
        max_length=20,
        default="EA1RKV",
        help_text="Club callsign",
    )
    club_name = models.CharField(
        max_length=200,
        default="Unión de Radioafeccionados de Vigo-Val Miñor",
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    locator = models.CharField(
        max_length=10,
        blank=True,
        help_text="Maidenhead grid locator (e.g., IN52JD)",
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("callsign"),
                FieldPanel("club_name"),
                FieldPanel("email"),
                FieldPanel("phone"),
                FieldPanel("address"),
            ],
            heading="Contact Information",
        ),
        MultiFieldPanel(
            [
                FieldPanel("locator"),
                FieldPanel("latitude"),
                FieldPanel("longitude"),
            ],
            heading="Location",
        ),
    ]

    class Meta:
        verbose_name = "Radioclub Settings"

