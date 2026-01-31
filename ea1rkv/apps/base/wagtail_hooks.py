"""Wagtail hooks for customizing the admin interface."""

from wagtail import hooks
from django.utils.html import format_html


@hooks.register("insert_global_admin_css")
def global_admin_css():
    """Add custom CSS to the Wagtail admin."""
    return format_html(
        "<style>"
        ".branding-logo {{ max-height: 40px; }}"
        "</style>"
    )
