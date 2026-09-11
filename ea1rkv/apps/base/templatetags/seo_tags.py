"""SEO metadata for public Wagtail pages."""

import json
from urllib.parse import urlsplit, urlunsplit

from django import template
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from django.utils.translation import get_language, override

from ea1rkv.apps.base.models import RadioclubSettings, SocialMediaSettings

register = template.Library()

SITE_NAME = "EA1RKV"
ORGANIZATION_NAME = "Unión de Radioafeccionados de Vigo-Val Miñor"
HOME_TITLES = {
    "es": "EA1RKV | Radioafición y radioclub en Vigo y Val Miñor",
    "gl": "EA1RKV | Radioafección e radioclub en Vigo e Val Miñor",
    "en": "EA1RKV | Amateur radio club in Vigo and Val Miñor",
}
DEFAULT_DESCRIPTIONS = {
    "es": "EA1RKV, radioclub de Vigo y Val Miñor: radioafición, repetidores, frecuencias, actividades, indicativos especiales y noticias.",
    "gl": "EA1RKV, radioclub de Vigo e Val Miñor: radioafección, repetidores, frecuencias, actividades, indicativos especiais e novas.",
    "en": "EA1RKV, the amateur radio club for Vigo and Val Miñor: repeaters, frequencies, activities, special callsigns and news.",
}


def _without_query(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _page_url(page, request):
    return _without_query(
        page.get_full_url(request=request) or request.build_absolute_uri(page.url)
    )


def _image_url(page, request):
    specific = page.specific
    for field in ("header_image", "cover_image", "hero_image", "photo"):
        image = getattr(specific, field, None)
        if image and image.file:
            return request.build_absolute_uri(image.file.url)
    return ""


@register.inclusion_tag("includes/seo_meta.html", takes_context=True)
def seo_meta(context):
    request = context["request"]
    page = context.get("page") or context.get("self")
    language = (get_language() or "es").split("-")[0]
    if page is None:
        return {"robots": "noindex,follow"}

    page = page.specific
    is_home = page._meta.label_lower == "home.homepage"
    editorial_title = (page.seo_title or "").strip()
    title = editorial_title or (
        HOME_TITLES.get(language, HOME_TITLES["es"])
        if is_home
        else f"{page.title} | {SITE_NAME}"
    )
    if is_home and editorial_title.casefold() in {"inicio", "home"}:
        title = HOME_TITLES.get(language, HOME_TITLES["es"])
    editorial_description = (
        page.search_description
        or getattr(page, "intro", "")
        or getattr(page, "summary", "")
    )
    description = (
        Truncator(strip_tags(str(editorial_description))).chars(180)
        if editorial_description
        else (DEFAULT_DESCRIPTIONS.get(language, DEFAULT_DESCRIPTIONS["es"]))
    )
    canonical = _page_url(page, request)
    image = _image_url(page, request)

    alternates = []
    for translated in (
        page.get_translations(inclusive=True).live().public().select_related("locale")
    ):
        code = translated.locale.language_code
        with override(code):
            alternates.append({"language": code, "url": _page_url(translated, request)})
    default_url = next(
        (item["url"] for item in alternates if item["language"] == "es"), canonical
    )

    club = RadioclubSettings.for_request(request)
    social = SocialMediaSettings.for_request(request)
    club_name = club.club_name or ORGANIZATION_NAME
    callsign = club.callsign or SITE_NAME
    canonical_parts = urlsplit(canonical)
    site_root = urlunsplit(
        (canonical_parts.scheme, canonical_parts.netloc, "/", "", "")
    )
    organization_id = site_root + "#organization"
    website_id = site_root + "#website"
    organization = {
        "@type": "Organization",
        "@id": organization_id,
        "name": club_name,
        "alternateName": callsign,
        "url": site_root,
        "description": DEFAULT_DESCRIPTIONS[language]
        if language in DEFAULT_DESCRIPTIONS
        else DEFAULT_DESCRIPTIONS["es"],
        "areaServed": [
            {"@type": "City", "name": "Vigo"},
            {"@type": "AdministrativeArea", "name": "Val Miñor"},
        ],
    }
    contact = {
        key: value
        for key, value in {
            "email": club.email,
            "telephone": club.phone,
        }.items()
        if value
    }
    if contact:
        organization["contactPoint"] = {"@type": "ContactPoint", **contact}
    if club.address:
        organization["address"] = {
            "@type": "PostalAddress",
            "streetAddress": club.address,
            "addressCountry": "ES",
        }
    if club.latitude is not None and club.longitude is not None:
        organization["location"] = {
            "@type": "Place",
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": club.latitude,
                "longitude": club.longitude,
            },
        }
    same_as = [
        value
        for value in (
            social.facebook,
            social.twitter,
            social.instagram,
            social.youtube,
            social.qrz,
        )
        if value
    ]
    if same_as:
        organization["sameAs"] = same_as

    graph = [
        organization,
        {
            "@type": "WebSite",
            "@id": website_id,
            "url": site_root,
            "name": f"{callsign} · {club_name}",
            "publisher": {"@id": organization_id},
            "inLanguage": [item["language"] for item in alternates] or [language],
        },
        {
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": title,
            "description": description,
            "isPartOf": {"@id": website_id},
            "about": {"@id": organization_id},
            "inLanguage": language,
        },
    ]
    breadcrumb_items = []
    for ancestor in page.get_ancestors(inclusive=True).live().public().specific():
        url = ancestor.get_full_url(request=request)
        if url:
            breadcrumb_items.append(
                {
                    "@type": "ListItem",
                    "position": len(breadcrumb_items) + 1,
                    "name": ancestor.title,
                    "item": _without_query(url),
                }
            )
    if len(breadcrumb_items) > 1:
        graph.append({"@type": "BreadcrumbList", "itemListElement": breadcrumb_items})
    if page._meta.label_lower == "blog.blogpage":
        article = {
            "@type": "BlogPosting",
            "@id": canonical + "#article",
            "mainEntityOfPage": {"@id": canonical + "#webpage"},
            "headline": page.title,
            "description": page.intro or description,
            "datePublished": page.date.isoformat(),
            "author": (
                {"@type": "Person", "name": page.author_name}
                if page.author_name
                else {"@id": organization_id}
            ),
            "publisher": {"@id": organization_id},
            "inLanguage": language,
        }
        if page.last_published_at:
            article["dateModified"] = page.last_published_at.isoformat()
        if image:
            article["image"] = image
        graph.append(article)

    structured_data = json.dumps(
        {"@context": "https://schema.org", "@graph": graph},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    return {
        "title": title,
        "description": description,
        "canonical": canonical,
        "alternates": alternates,
        "default_url": default_url,
        "language": language,
        "og_locale": {"es": "es_ES", "gl": "gl_ES", "en": "en_GB"}.get(
            language, language
        ),
        "image": image,
        "is_article": page._meta.label_lower == "blog.blogpage",
        "robots": "noindex,follow"
        if request.GET
        else "index,follow,max-image-preview:large",
        "google_site_verification": settings.GOOGLE_SITE_VERIFICATION,
        "structured_data": mark_safe(structured_data),
    }
