import logging
import os
import tempfile

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import RestoreBackupForm
from .services import (
    BackupError,
    backup_root,
    create_backup,
    operation_lock,
    resolve_saved_backup,
    restore_backup,
    saved_backups,
    validate_backup,
)

logger = logging.getLogger(__name__)


def _require_superuser(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise PermissionDenied


@require_http_methods(["GET"])
def index(request):
    _require_superuser(request)
    return render(
        request,
        "backups/index.html",
        {"backups": saved_backups(), "restore_form": RestoreBackupForm()},
    )


@require_POST
def create(request):
    _require_superuser(request)
    try:
        with operation_lock():
            path = create_backup(f"admin:{request.user.get_username()}")
    except BackupError as exc:
        logger.exception("Backup creation failed")
        messages.error(request, str(exc))
        return redirect("admin_backups:index")
    logger.warning("Backup %s created by %s", path.name, request.user.get_username())
    messages.success(request, f"Copia {path.name} creada correctamente.")
    return redirect("admin_backups:index")


@require_http_methods(["GET"])
def download(request, name):
    _require_superuser(request)
    try:
        path = resolve_saved_backup(name)
    except FileNotFoundError as exc:
        raise Http404 from exc
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)


@require_POST
@transaction.non_atomic_requests
def restore(request):
    _require_superuser(request)
    form = RestoreBackupForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "backups/index.html", {"backups": saved_backups(), "restore_form": form}, status=400)
    upload = form.cleaned_data["backup_file"]
    if upload.size > settings.BACKUP_MAX_UPLOAD_SIZE:
        messages.error(request, "La copia supera el tamaño máximo permitido.")
        return redirect("admin_backups:index")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=backup_root(), suffix=".upload", delete=False) as temporary:
            temporary_path = temporary.name
            for chunk in upload.chunks():
                temporary.write(chunk)
        with operation_lock():
            validate_backup(temporary_path)
            safety = create_backup(f"pre-restore:{request.user.get_username()}")
            restore_backup(temporary_path)
        logger.critical("Backup restored by %s; safety backup: %s", request.user.get_username(), safety.name)
        messages.success(request, f"Restauración completada. Copia previa conservada: {safety.name}.")
    except BackupError as exc:
        logger.exception("Backup restore failed")
        messages.error(request, str(exc))
    finally:
        if temporary_path:
            os.unlink(temporary_path)
    return redirect("admin_backups:index")
