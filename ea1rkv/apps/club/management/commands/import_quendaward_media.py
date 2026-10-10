"""Import an export directory as a Wagtail draft, preserving existing content."""
import hashlib
import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.html import escape
from PIL import Image as PillowImage
from wagtail.documents import get_document_model
from wagtail.images import get_image_model

from ea1rkv.apps.club.models import CallsignMedia, SpecialCallsignPage, youtube_video_id


class Command(BaseCommand):
    help = "Importa quendaward_media como borrador. Sin --apply sólo valida y muestra el plan."

    def add_arguments(self, parser):
        parser.add_argument("directory")
        parser.add_argument("--page-id", required=True, type=int)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        stored = []
        try:
            with transaction.atomic():
                self.run_import(options, stored)
        except Exception as exc:
            # SQL rollback does not remove files already written to storage.
            for storage, name in stored:
                try:
                    storage.delete(name)
                except Exception:
                    self.stderr.write(f"No se pudo limpiar el archivo nuevo: {name}")
            if isinstance(exc, CommandError):
                raise
            raise CommandError(str(exc)) from exc

    def run_import(self, options, stored):
        root = Path(options["directory"]).resolve()
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("format") != "quendaward-media-v1":
            raise CommandError("Formato de exportación desconocido.")
        source = manifest.get("source")
        if not isinstance(source, str) or not source.strip():
            raise CommandError("Falta el identificador estable del origen.")
        page = SpecialCallsignPage.objects.select_for_update().get(pk=options["page_id"])
        if page.locked or page.current_workflow_state:
            raise CommandError("La página está bloqueada o en un flujo de revisión.")
        page = page.get_latest_revision_as_object()
        existing = list(page.media_items.all())
        known = {item.source_key for item in existing if item.source_key}
        rows = manifest["items"]
        if not isinstance(rows, list) or not rows:
            raise CommandError("La exportación no contiene elementos.")
        # Match the source's group order, then its existing media order.
        rows = sorted(enumerate(rows), key=lambda pair: (
            pair[1].get("group_order") if pair[1].get("group_order") is not None else 999999,
            pair[0],
        ))
        pending, errors, seen = [], [], set()
        self.stdout.write(f"Origen: {manifest['award']['name']} → página {page.pk}: {page.title} ({page.locale})")
        for _, row in rows:
            key = f"{source}:{manifest['award']['id']}:{row['id']}"
            if key in seen:
                errors.append(f"ID repetido en exportación: {key}")
                continue
            seen.add(key)
            if key in known:
                self.stdout.write(f"OMITIR {row['id']}: ya importado")
                continue
            try:
                item = CallsignMedia(
                    page=page, source_key=key, kind=row["media_type"], title=row["title"],
                    group=row.get("group", ""),
                    description="<p>" + str(escape(row.get("description") or "")).replace("\n", "<br/>") + "</p>",
                    youtube_url=row.get("youtube_url") or "",
                )
                # Validate text lengths and choices before writing any files.
                item.clean_fields(exclude=["image", "asset", "sort_order"])
                path = None
                if item.kind == "youtube":
                    if not youtube_video_id(item.youtube_url):
                        raise ValueError("Enlace de YouTube inválido")
                else:
                    path = (root / row["path"]).resolve()
                    if not path.is_relative_to(root) or not path.is_file():
                        raise ValueError("Archivo ausente o fuera del directorio")
                    with path.open("rb") as handle:
                        digest = hashlib.file_digest(handle, "sha256").hexdigest()
                    if digest != row.get("sha256"):
                        raise ValueError("El archivo no coincide con su SHA-256")
                    if item.kind == "image":
                        with PillowImage.open(path) as image:
                            image.verify()
                    allowed = {"video": CallsignMedia.VIDEO_EXTENSIONS, "audio": CallsignMedia.AUDIO_EXTENSIONS}.get(item.kind)
                    if allowed and path.suffix.lower().lstrip(".") not in allowed:
                        raise ValueError("Formato no compatible; convertir antes de importar")
                pending.append((item, path, row))
                self.stdout.write(f"AÑADIR {row['id']}: {item.kind} | {item.group} | {item.title}")
            except (ValidationError, ValueError, KeyError, OSError) as exc:
                errors.append(f"Elemento {row.get('id')}: {exc}")
        if errors:
            raise CommandError("No se ha importado nada:\n" + "\n".join(errors))
        self.stdout.write(f"Nuevos: {len(pending)}. Ya importados: {len(seen & known)}.")
        if not options["apply"]:
            self.stdout.write("Previsualización sin cambios. Añade --apply para crear el borrador.")
            return
        if not pending:
            return
        next_order = max((item.sort_order or 0 for item in existing), default=-1) + 1
        for offset, (item, path, row) in enumerate(pending):
            if path:
                model = get_image_model() if item.kind == "image" else get_document_model()
                asset = model(title=item.title)
                name = Path(row.get("original_filename") or path.name).name
                with path.open("rb") as handle:
                    asset.file.save(name, File(handle), save=False)
                stored.append((asset.file.storage, asset.file.name))
                asset.save()
                if item.kind == "image":
                    item.image = asset
                else:
                    item.asset = asset
            item.sort_order = next_order + offset
            item.full_clean()
            page.media_items.add(item)
        revision = page.save_revision()
        self.stdout.write(self.style.SUCCESS(
            f"Borrador {revision.pk} creado con {len(pending)} elementos nuevos. "
            f"Revisa /admin/pages/{page.pk}/edit/ y publica desde Wagtail."
        ))
