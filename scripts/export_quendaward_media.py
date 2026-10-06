"""Run inside quendaward-media; export one award without altering its databases."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3


def readonly(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def export(award_id, output, source):
    root = Path(os.environ.get("MEDIA_DIR", "/data/media")).resolve()
    with readonly(os.environ.get("MEDIA_DB_PATH", "/data/media.db")) as db:
        rows = [dict(r) for r in db.execute(
            "SELECT * FROM media WHERE award_id=? ORDER BY COALESCE(sort_order,999999), uploaded_at DESC, id",
            (award_id,),
        )]
        groups = {r["id"]: dict(r) for r in db.execute(
            "SELECT * FROM media_groups WHERE award_id=?", (award_id,),
        )}
    with readonly(os.environ.get("QUENDAWARD_DB_PATH", "/quendaward_data/ham_coordinator.db")) as db:
        award = db.execute("SELECT id, name FROM awards WHERE id=?", (award_id,)).fetchone()
    if not award or not rows:
        raise ValueError("Indicativo inexistente o sin medios.")
    # Refuse missing files before creating an export directory.
    for row in rows:
        if row["media_type"] != "youtube":
            file = (root / row["filename"]).resolve()
            if not file.is_relative_to(root) or not file.is_file():
                raise ValueError(f"Archivo ausente o ruta inválida: {row['id']} {row['filename']}")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "files").mkdir()
    items = []
    for row in rows:
        group = groups.get(row.get("group_id"), {})
        row["group"] = group.get("name", "")
        row["group_order"] = group.get("sort_order")
        if row["media_type"] != "youtube":
            original = root / row["filename"]
            name = f"{row['id']}{original.suffix.lower()}"
            target = output / "files" / name
            shutil.copyfile(original, target)
            with target.open("rb") as handle:
                row["sha256"] = hashlib.file_digest(handle, "sha256").hexdigest()
            row["path"] = f"files/{name}"
        items.append(row)
    manifest = {"format": "quendaward-media-v1", "source": source,
                "award": dict(award), "items": items}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exportados {len(items)} elementos de {award['name']} a {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Listar IDs de indicativos")
    parser.add_argument("--award-id", type=int)
    parser.add_argument("--output")
    parser.add_argument("--source", default="quendaward_media", help="Identificador estable de esta instalación")
    args = parser.parse_args()
    if args.list:
        with readonly(os.environ.get("QUENDAWARD_DB_PATH", "/quendaward_data/ham_coordinator.db")) as db:
            for row in db.execute("SELECT id, name FROM awards ORDER BY name"):
                print(row["id"], row["name"])
    elif args.award_id is not None and args.output:
        export(args.award_id, args.output, args.source)
    else:
        parser.error("Usa --list o --award-id ID --output DIRECTORIO_NUEVO")


if __name__ == "__main__":
    main()
