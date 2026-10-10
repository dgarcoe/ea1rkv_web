import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
import zipfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.db import connections

FORMAT_VERSION = 1
ARCHIVE_SUFFIX = ".ea1rkv"
MANIFEST_NAME = "manifest.json"
DATABASE_NAME = "database.dump"
MAX_ARCHIVE_MEMBERS = 100_000


class BackupError(Exception):
    pass


class BackupBusyError(BackupError):
    pass


def backup_root():
    root = Path(settings.BACKUP_ROOT).resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


@contextmanager
def operation_lock():
    """Prevent two Gunicorn workers from backing up/restoring concurrently."""
    import fcntl

    lock_path = backup_root() / ".operation.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise BackupBusyError(
                "Ya hay una copia o restauración en curso. Inténtalo más tarde."
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def private_root():
    return (Path(settings.BASE_DIR) / "privatefiles").resolve()


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _database_engine():
    return settings.DATABASES["default"]["ENGINE"].rsplit(".", 1)[-1]


def _pg_environment(config):
    environment = os.environ.copy()
    if config.get("PASSWORD"):
        environment["PGPASSWORD"] = str(config["PASSWORD"])
    return environment


def _database_dump(destination):
    config = settings.DATABASES["default"]
    engine = _database_engine()
    if engine == "sqlite3":
        source = Path(config["NAME"])
        source_connection = sqlite3.connect(source)
        target_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(target_connection)
        finally:
            target_connection.close()
            source_connection.close()
        return "sqlite3"
    if engine != "postgresql":
        raise BackupError(f"Motor de base de datos no compatible: {engine}")
    command = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(destination),
        "--host",
        str(config["HOST"]),
        "--port",
        str(config["PORT"]),
        "--username",
        str(config["USER"]),
        str(config["NAME"]),
    ]
    _run(command, _pg_environment(config), "No se pudo exportar PostgreSQL")
    return "postgresql"


def _run(command, environment, message):
    try:
        subprocess.run(
            command,
            check=True,
            env=environment,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise BackupError(f"{message}: falta la herramienta {command[0]}.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise BackupError(f"{message}: {detail[:1000]}") from exc


def _add_tree(archive, root, prefix):
    root = Path(root)
    if not root.exists():
        return 0
    count = 0
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            archive.write(path, (PurePosixPath(prefix) / path.relative_to(root)).as_posix())
            count += 1
    return count


def create_backup(label="manual"):
    root = backup_root()
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    final_path = root / f"ea1rkv-{timestamp}-{uuid.uuid4().hex[:8]}{ARCHIVE_SUFFIX}"
    with tempfile.TemporaryDirectory(dir=root, prefix=".creating-") as temporary:
        temporary = Path(temporary)
        database_path = temporary / DATABASE_NAME
        database_engine = _database_dump(database_path)
        manifest = {
            "format": "ea1rkv-backup",
            "format_version": FORMAT_VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": label,
            "database_engine": database_engine,
            "database_sha256": _sha256(database_path),
        }
        partial = temporary / "archive.partial"
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            archive.write(database_path, DATABASE_NAME)
            manifest["media_files"] = _add_tree(archive, settings.MEDIA_ROOT, "media")
            manifest["private_files"] = _add_tree(archive, private_root(), "privatefiles")
            archive.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, ensure_ascii=False))
        os.chmod(partial, 0o600)
        partial.replace(final_path)
    return final_path


def _safe_member(member):
    path = PurePosixPath(member.filename)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not member.is_dir()
        and (member.external_attr >> 16) & 0o170000 != 0o120000
    )


def validate_backup(path):
    path = Path(path)
    if path.stat().st_size > settings.BACKUP_MAX_UPLOAD_SIZE:
        raise BackupError("La copia supera el tamaño máximo permitido.")
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS or any(not _safe_member(item) for item in members):
                raise BackupError("La copia contiene rutas no permitidas.")
            if sum(item.file_size for item in members) > settings.BACKUP_MAX_UPLOAD_SIZE:
                raise BackupError("El contenido descomprimido supera el tamaño máximo permitido.")
            names = {item.filename for item in members}
            if not {MANIFEST_NAME, DATABASE_NAME}.issubset(names):
                raise BackupError("El archivo no contiene una copia completa.")
            manifest = json.loads(archive.read(MANIFEST_NAME))
            if manifest.get("format") != "ea1rkv-backup" or manifest.get("format_version") != FORMAT_VERSION:
                raise BackupError("El formato o la versión de la copia no son compatibles.")
            digest = hashlib.sha256()
            with archive.open(DATABASE_NAME) as database:
                for chunk in iter(lambda: database.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != manifest.get("database_sha256"):
                raise BackupError("La base de datos de la copia está dañada.")
            if manifest.get("database_engine") != _database_engine():
                raise BackupError("La copia usa un motor de base de datos diferente.")
            damaged = archive.testzip()
            if damaged:
                raise BackupError(f"El archivo {damaged} está dañado.")
            return manifest
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError) as exc:
        raise BackupError("El archivo no es una copia EA1RKV válida.") from exc


def _extract_content(archive, prefix, destination):
    staging = Path(tempfile.mkdtemp(prefix=f".{prefix}-", dir=destination.parent))
    try:
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if len(path.parts) < 2 or path.parts[0] != prefix or member.is_dir():
                continue
            relative = Path(*path.parts[1:])
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
        destination.mkdir(parents=True, exist_ok=True)
        for child in destination.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        for child in staging.iterdir():
            shutil.move(str(child), destination / child.name)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def restore_backup(path):
    """Restore a validated archive. Call only after creating a safety backup."""
    validate_backup(path)
    config = settings.DATABASES["default"]
    root = backup_root()
    marker = root / ".restore-in-progress"
    marker.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory(dir=root, prefix=".restoring-") as temporary:
            temporary = Path(temporary)
            with zipfile.ZipFile(path) as archive:
                database_path = temporary / DATABASE_NAME
                with archive.open(DATABASE_NAME) as source, database_path.open("wb") as output:
                    shutil.copyfileobj(source, output)
                connections.close_all()
                if _database_engine() == "postgresql":
                    command = [
                        "pg_restore",
                        "--clean",
                        "--if-exists",
                        "--no-owner",
                        "--no-privileges",
                        "--exit-on-error",
                        "--host",
                        str(config["HOST"]),
                        "--port",
                        str(config["PORT"]),
                        "--username",
                        str(config["USER"]),
                        "--dbname",
                        str(config["NAME"]),
                        str(database_path),
                    ]
                    _run(command, _pg_environment(config), "No se pudo restaurar PostgreSQL")
                else:
                    shutil.copy2(database_path, config["NAME"])
                _extract_content(archive, "media", Path(settings.MEDIA_ROOT).resolve())
                _extract_content(archive, "privatefiles", private_root())
    finally:
        marker.unlink(missing_ok=True)
        connections.close_all()


def saved_backups():
    result = []
    for path in sorted(backup_root().glob(f"*{ARCHIVE_SUFFIX}"), reverse=True):
        result.append({"name": path.name, "size": path.stat().st_size, "modified": datetime.fromtimestamp(path.stat().st_mtime, UTC)})
    return result


def resolve_saved_backup(name):
    if Path(name).name != name or not name.endswith(ARCHIVE_SUFFIX):
        raise FileNotFoundError(name)
    path = backup_root() / name
    if not path.is_file():
        raise FileNotFoundError(name)
    return path
