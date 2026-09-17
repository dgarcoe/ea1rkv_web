"""Keep published content and each historical draft when unifying the library."""
from html import escape

from django.db import migrations


def legacy_items(photos, downloads, image_titles, document_titles, page_id):
    items = []
    for photo in photos:
        image_id = photo.get("image")
        if not image_id:
            continue
        items.append({
            "kind": "image", "title": image_titles.get(image_id, "Imagen")[:255],
            "description": f'<p>{escape(photo.get("caption") or "")}</p>' if photo.get("caption") else "",
            "image": image_id, "asset": None, "youtube_url": "",
            "group": (photo.get("group") or "").strip(), "credit": photo.get("credit") or "",
        })
    for document in downloads:
        document_id = document.get("document")
        if not document_id:
            continue
        items.append({
            "kind": "document", "title": document_titles.get(document_id, "Documento")[:255],
            "description": f'<p>{escape(document.get("description") or "")}</p>' if document.get("description") else "",
            "image": None, "asset": document_id, "youtube_url": "", "group": "", "credit": "",
        })
    return [{"pk": None, "page": page_id, "sort_order": index, **item}
            for index, item in enumerate(items)]


def populate_library(apps, schema_editor):
    alias = schema_editor.connection.alias
    Page = apps.get_model("club", "SpecialCallsignPage")
    Photo = apps.get_model("club", "CallsignPhoto")
    Download = apps.get_model("club", "CallsignDownload")
    Media = apps.get_model("club", "CallsignMedia")
    image_titles = dict(apps.get_model("wagtailimages", "Image").objects.using(alias).values_list("pk", "title"))
    document_titles = dict(apps.get_model("wagtaildocs", "Document").objects.using(alias).values_list("pk", "title"))
    for page in Page.objects.using(alias).all().iterator():
        if Media.objects.using(alias).filter(page_id=page.pk).exists():
            continue
        photos = Photo.objects.using(alias).filter(page_id=page.pk).order_by("sort_order", "pk").values("image", "caption", "credit", "group")
        documents = Download.objects.using(alias).filter(page_id=page.pk).order_by("sort_order", "pk").values("document", "description")
        for item in legacy_items(photos, documents, image_titles, document_titles, page.pk):
            Media.objects.using(alias).create(
                page_id=item["page"], sort_order=item["sort_order"], kind=item["kind"],
                title=item["title"], description=item["description"], credit=item["credit"],
                group=item["group"], image_id=item["image"], asset_id=item["asset"],
            )
    content_type = apps.get_model("contenttypes", "ContentType").objects.using(alias).filter(
        app_label="club", model="specialcallsignpage").first()
    if content_type is None:
        return
    revisions = apps.get_model("wagtailcore", "Revision").objects.using(alias).filter(content_type_id=content_type.pk)
    for revision in revisions.iterator():
        data = revision.content.copy()
        if "media_items" in data:
            continue
        data["media_items"] = legacy_items(data.get("photos", []), data.get("downloads", []),
                                            image_titles, document_titles, int(revision.object_id))
        revisions.filter(pk=revision.pk).update(content=data)


class Migration(migrations.Migration):
    dependencies = [("club", "0003_callsignmedia")]
    operations = [migrations.RunPython(populate_library, migrations.RunPython.noop)]
