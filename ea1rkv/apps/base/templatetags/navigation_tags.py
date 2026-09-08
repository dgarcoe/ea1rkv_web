"""Template tags for site navigation."""

from django import template

from wagtail.models import Page, Site

register = template.Library()


@register.simple_tag(takes_context=True)
def get_site_root(context):
    """Return the site root page for the current site."""
    return Site.find_for_request(context["request"]).root_page


@register.inclusion_tag("includes/main_menu.html", takes_context=True)
def main_menu(context, parent=None, calling_page=None):
    """Render the main navigation menu."""
    if parent is None:
        parent = get_site_root(context)

    menuitems = parent.get_children().live().public().in_menu()

    for menuitem in menuitems:
        menuitem.active = (
            calling_page is not None
            and calling_page.url_path.startswith(menuitem.url_path)
        )

    return {
        "calling_page": calling_page,
        "menuitems": menuitems,
        "request": context["request"],
    }


@register.inclusion_tag("includes/breadcrumbs.html", takes_context=True)
def breadcrumbs(context, calling_page=None):
    """Render breadcrumb navigation."""
    if calling_page is None:
        return {"ancestors": [], "request": context["request"]}

    site_root = get_site_root(context)
    ancestors = (
        Page.objects.ancestor_of(calling_page, inclusive=True)
        .descendant_of(site_root)
        .live()
    )

    return {
        "ancestors": ancestors,
        "request": context["request"],
    }

