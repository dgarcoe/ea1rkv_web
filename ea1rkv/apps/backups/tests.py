import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .services import BackupError, create_backup, validate_backup


class BackupTests(TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.media = Path(self.temporary.name) / "media"
        self.private = Path(self.temporary.name) / "privatefiles"
        self.backups = Path(self.temporary.name) / "backups"
        self.media.mkdir()
        self.private.mkdir()
        self.backups.mkdir()
        (self.media / "photo.jpg").write_bytes(b"image")
        (self.private / "minutes.pdf").write_bytes(b"private")
        self.settings = override_settings(MEDIA_ROOT=self.media, BACKUP_ROOT=self.backups)
        self.settings.enable()
        self.private_patch = patch("ea1rkv.apps.backups.services.private_root", return_value=self.private)
        self.private_patch.start()

    def tearDown(self):
        self.private_patch.stop()
        self.settings.disable()
        self.temporary.cleanup()

    def test_create_and_validate_complete_archive(self):
        path = create_backup("test")
        manifest = validate_backup(path)
        self.assertEqual(manifest["format_version"], 1)
        with zipfile.ZipFile(path) as archive:
            self.assertIn("media/photo.jpg", archive.namelist())
            self.assertIn("privatefiles/minutes.pdf", archive.namelist())

    def test_rejects_tampered_database(self):
        path = self.backups / "bad.ea1rkv"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("database.dump", b"tampered")
            archive.writestr("manifest.json", json.dumps({"format": "ea1rkv-backup", "format_version": 1, "database_engine": "sqlite3", "database_sha256": "bad"}))
        with self.assertRaises(BackupError):
            validate_backup(path)

    def test_only_superusers_can_access_admin_backup_centre(self):
        user = get_user_model().objects.create_user(
            "editor", password="secret", is_staff=True
        )
        self.client.force_login(user)
        self.assertNotEqual(
            self.client.get(reverse("admin_backups:index")).status_code, 200
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("admin_backups:index")).status_code, 200)
