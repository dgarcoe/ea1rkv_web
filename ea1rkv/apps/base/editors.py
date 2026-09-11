"""Classic HTML editor with reversible Wagtail image and link references."""
from urllib.parse import urlsplit

import bleach
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
from bs4.dammit import EntitySubstitution
from django import forms
from django.urls import reverse
from django.templatetags.static import static
from wagtail.rich_text import expand_db_html
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter


class WagtailHTMLFormatter(HTMLFormatter):
    def quoted_attribute_value(self, value):
        return '"' + value.replace('"', '&quot;') + '"'


HTML_FORMATTER = WagtailHTMLFormatter(entity_substitution=EntitySubstitution.substitute_xml)


def editor_html(value):
    soup = BeautifulSoup(str(value or ""), "html.parser")
    for embed in soup.find_all("embed"):
        if embed.get("embedtype") == "image":
            expanded = BeautifulSoup(expand_db_html(embed.decode(formatter=HTML_FORMATTER)), "html.parser").find("img")
            if expanded:
                expanded["alt"] = embed.get("alt", "")
                expanded["data-wagtail-image"] = embed.get("id", "")
                expanded["data-wagtail-format"] = embed.get("format", "fullwidth")
                embed.replace_with(expanded)
        elif embed.get("embedtype") == "media":
            placeholder = soup.new_tag("span")
            placeholder["data-wagtail-media"] = embed.get("url", "")
            placeholder["contenteditable"] = "false"
            placeholder.string = "Contenido multimedia: " + embed.get("url", "")
            embed.replace_with(placeholder)
    for link in soup.find_all("a", linktype=True):
        expanded = BeautifulSoup(expand_db_html(link.decode(formatter=HTML_FORMATTER)), "html.parser").find("a")
        link["href"] = expanded.get("href", "#") if expanded else "#"
    return soup.decode(formatter=HTML_FORMATTER)


def database_html(value):
    # Do not trust HTML submitted directly, including the editor's source dialog.
    cleaned = bleach.clean(
        BeautifulSoup(value or "", "html.parser").decode(formatter=HTML_FORMATTER),
        tags=["p", "br", "h2", "h3", "h4", "strong", "b", "em", "i", "u", "s",
              "blockquote", "ul", "ol", "li", "a", "img", "span", "table", "thead",
              "tbody", "tr", "th", "td", "caption", "hr", "sub", "sup", "pre", "code"],
        attributes={"a": ["href", "title", "linktype", "id"],
                    "img": ["src", "alt", "data-wagtail-image", "data-wagtail-format"],
                    "span": ["data-wagtail-media"], "td": ["colspan", "rowspan"],
                    "th": ["colspan", "rowspan", "scope"]},
        protocols=["http", "https", "mailto", "tel"], strip=True,
    )
    soup = BeautifulSoup(cleaned, "html.parser")
    for image in soup.find_all("img", attrs={"data-wagtail-image": True}):
        image_id = image.get("data-wagtail-image", "")
        if not image_id.isdigit():
            image.decompose()
            continue
        embed = soup.new_tag("embed")
        embed.attrs = {"embedtype": "image", "id": image_id,
                       "format": image.get("data-wagtail-format", "fullwidth")
                       if image.get("data-wagtail-format") in ("fullwidth", "left", "right") else "fullwidth",
                       "alt": image.get("alt", "")}
        image.replace_with(embed)
    for placeholder in soup.find_all("span", attrs={"data-wagtail-media": True}):
        url = placeholder["data-wagtail-media"]
        try:
            valid_url = urlsplit(url).scheme in ("http", "https")
        except ValueError:
            valid_url = False
        if valid_url:
            embed = soup.new_tag("embed", embedtype="media", url=url)
            placeholder.replace_with(embed)
        else:
            placeholder.decompose()
    for link in soup.find_all("a", linktype=True):
        if link.get("linktype") in ("page", "document") and link.get("id", "").isdigit():
            link.attrs = {"linktype": link["linktype"], "id": link["id"]}
        else:
            link.attrs.pop("linktype", None)
            link.attrs.pop("id", None)
    # Wagtail's reference scanner expects double quotes and self-closing embeds.
    return soup.decode(formatter=HTML_FORMATTER)


class ClassicRichTextWidget(forms.Textarea):
    accepts_features = True

    def __init__(self, attrs=None, features=None, options=None):
        super().__init__({"class": "ea1rkv-classic-editor", "rows": 18, **(attrs or {})})

    def format_value(self, value):
        return editor_html(value)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"].update({
            "data-tinymce-base": static("tinymce/tinymce.min.js").rsplit("/", 1)[0],
            "data-image-chooser": reverse("wagtailimages_chooser:choose"),
            "data-document-chooser": reverse("wagtaildocs_chooser:choose"),
        })
        return context

    def value_from_datadict(self, data, files, name):
        return database_html(super().value_from_datadict(data, files, name))

    class Media:
        js = ["tinymce/tinymce.min.js", "wagtailadmin/js/modal-workflow.js",
              "wagtailimages/js/image-chooser-modal.js", "wagtaildocs/js/document-chooser-modal.js",
              "js/classic-editor.js"]


register(WidgetAdapter(), ClassicRichTextWidget)
