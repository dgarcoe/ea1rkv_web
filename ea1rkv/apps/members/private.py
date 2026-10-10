"""Private files are deliberately stored outside MEDIA_ROOT."""
import secrets
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.BASE_DIR / "privatefiles")

    def url(self, name):
        raise ValueError("Los documentos privados sólo se descargan desde la zona de socios.")


def private_upload(instance, filename):
    return secrets.token_hex(20) + Path(filename).suffix.lower()
