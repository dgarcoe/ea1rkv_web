"""Frozen conversion helpers for the move from blocks to a single editor."""
import json
from html import escape
from urllib.parse import urlsplit


def text(value):
    return escape(str(value or ""), quote=True)


def paragraph(value):
    return f"<p>{text(value)}</p>" if value else ""


def link(url, label):
    if url and urlsplit(str(url)).scheme.lower() in ("", "http", "https", "mailto"):
        return f'<p><a href="{text(url)}">{text(label)}</a></p>'
    return paragraph(label)


def image(value):
    if isinstance(value, dict):
        value = value.get("id")
    return f'<embed embedtype="image" id="{int(value)}" format="fullwidth" alt=""/>' if value else ""


def convert(body, intro=""):
    if hasattr(body, "raw_data"):
        body = list(body.raw_data)
    if isinstance(body, str):
        body = json.loads(body) if body else []
    parts = [str(intro or "")]
    for block in body or []:
        kind, value = block["type"], block["value"]
        if kind == "paragraph":
            parts.append(str(value or ""))
        elif kind == "heading":
            size = value.get("size", "h2")
            size = size if size in ("h2", "h3") else "h3"
            parts.append(f'<{size}>{text(value.get("heading_text"))}</{size}>')
        elif kind == "image":
            parts.extend([image(value.get("image")), paragraph(value.get("caption")), paragraph(value.get("attribution"))])
        elif kind == "quote":
            parts.extend([paragraph(value.get("text")), paragraph(value.get("author"))])
        elif kind == "cta":
            parts.extend([value.get("text", ""), link(value.get("button_url"), value.get("button_text"))])
        elif kind == "cards":
            for card in value.get("cards", []):
                card = card.get("value", card)
                parts.extend([f'<h3>{text(card.get("title"))}</h3>', image(card.get("image")), paragraph(card.get("text"))])
                if card.get("link"):
                    parts.append(link(card["link"], card.get("title")))
        elif kind == "embed":
            if urlsplit(str(value)).scheme.lower() in ("http", "https"):
                parts.append(f'<embed embedtype="media" url="{text(value)}"/>')
        else:
            raise ValueError(f"Unknown legacy block: {kind}. Original content has not been removed.")
    return "".join(parts)


def migrate_content(apps, schema_editor, app_label, model_name):
    alias = schema_editor.connection.alias
    model = apps.get_model(app_label, model_name)
    for page in model.objects.using(alias).all().iterator():
        if not page.content:
            model.objects.using(alias).filter(pk=page.pk).update(
                content=convert(page.body, getattr(page, "about_text", ""))
            )
    content_type = apps.get_model("contenttypes", "ContentType").objects.using(alias).filter(app_label=app_label, model=model_name.lower()).first()
    if content_type is None:  # Fresh installations have no page revisions yet.
        return
    revisions = apps.get_model("wagtailcore", "Revision").objects.using(alias).filter(content_type_id=content_type.pk)
    for revision in revisions.iterator():
        data = revision.content.copy()
        if "content" not in data:
            data["content"] = convert(data.get("body"), data.get("about_text", ""))
            revisions.filter(pk=revision.pk).update(content=data)
