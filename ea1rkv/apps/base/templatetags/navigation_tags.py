"""Template tags for site navigation."""

from django import template
from django.utils.translation import get_language, override

from wagtail.models import Page, Site

register = template.Library()


@register.simple_tag(takes_context=True)
def get_site_root(context):
    """Return the site root page for the current site."""
    site = Site.find_for_request(context["request"])
    if site is None:
        return None
    root = site.root_page
    translated = root.get_translations(inclusive=True).live().public().filter(
        locale__language_code=get_language()
    ).first()
    return translated or root


@register.inclusion_tag("includes/main_menu.html", takes_context=True)
def main_menu(context, parent=None, calling_page=None):
    """Render the main navigation menu."""
    if parent is None:
        parent = get_site_root(context)

    if parent is None:
        return {"menuitems": [], "request": context["request"]}
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



@register.inclusion_tag("includes/language_switcher.html", takes_context=True)
def language_switcher(context):
    page = context.get("page")
    options = []
    translations = {}
    if page:
        translations = {
            item.locale.language_code: item
            for item in page.get_translations(inclusive=True).live().public().select_related("locale")
        }
    for code, label in (("gl", "Galego"), ("es", "Español"), ("en", "English")):
        target = translations.get(code)
        url = None
        if target:
            with override(code):
                url = target.get_url(context["request"])
        options.append({"code": code, "label": label, "url": url,
                        "active": code == get_language()})
    return {"options": options}


@register.simple_tag
def home_label():
    return {"gl": "Inicio", "es": "Inicio", "en": "Home"}.get(get_language(), "Inicio")
