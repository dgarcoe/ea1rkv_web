"""Publication integration for the agenda."""

from django.dispatch import receiver
from wagtail.signals import page_published

from .translation import replicate_event_translations


@receiver(page_published)
def replicate_published_event_translations(sender, instance, **kwargs):
    replicate_event_translations(instance.specific)
