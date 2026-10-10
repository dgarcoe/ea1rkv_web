from io import StringIO
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from PIL import Image
from wagtail.documents import get_document_model
from wagtail.images import get_image_model

from scripts.export_quendaward_media import export
from .models import CallsignsPage, SpecialCallsignPage


class QuendawardImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_radioclub", stdout=StringIO())
        index = CallsignsPage.objects.get()
        cls.page = index.add_child(instance=SpecialCallsignPage(
            title="EG1912T", callsign="EG1912T", slug="migration-test",
            locale=index.locale, live=False,
        ))
        cls.page.save_revision().publish()

    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        settings = override_settings(MEDIA_ROOT=self.root / "wagtail")
        settings.enable()
        self.addCleanup(settings.disable)
        files = self.root / "media"
        files.mkdir()
        Image.new("RGB", (20, 30)).save(files / "test.png")
        for name in ("test.pdf", "test.mp4", "test.mp3"):
            (files / name).write_bytes(b"fixture")
        with sqlite3.connect(self.root / "media.db") as db:
            db.execute("CREATE TABLE media_groups (id INTEGER, award_id INTEGER, name TEXT, sort_order INTEGER)")
            db.execute("INSERT INTO media_groups VALUES (1, 7, 'Historia', 1)")
            db.execute("CREATE TABLE media (id INTEGER, award_id INTEGER, title TEXT, description TEXT, media_type TEXT, filename TEXT, original_filename TEXT, uploaded_at TEXT, sort_order INTEGER, group_id INTEGER, youtube_url TEXT)")
            for i, (kind, name) in enumerate(zip(
                ("image", "document", "video", "audio", "youtube"),
                ("test.png", "test.pdf", "test.mp4", "test.mp3", ""),
            ), 1):
                db.execute("INSERT INTO media VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                    i, 7, f"Item {i}", "Línea 1\n<script>texto</script>", kind, name,
                    name, "2026-01-01", i, 1, "https://youtu.be/abcdefghijk" if kind == "youtube" else "",
                ))
        with sqlite3.connect(self.root / "awards.db") as db:
            db.execute("CREATE TABLE awards (id INTEGER, name TEXT)")
            db.execute("INSERT INTO awards VALUES (7, 'EG1912T')")
        self.bundle = self.root / "export"
        with patch.dict(os.environ, {
            "MEDIA_DB_PATH": str(self.root / "media.db"), "MEDIA_DIR": str(files),
            "QUENDAWARD_DB_PATH": str(self.root / "awards.db"),
        }):
            export(7, self.bundle, "quendaward_media")

    def run_import(self, apply=False):
        call_command("import_quendaward_media", str(self.bundle), page_id=self.page.pk,
                     apply=apply, stdout=StringIO())

    def test_preview_and_repeat_and_publish(self):
        revisions = self.page.revisions.count()
        self.run_import()
        self.assertEqual(self.page.revisions.count(), revisions)
        self.assertEqual(get_image_model().objects.count(), 0)
        self.run_import(True)
        self.page.refresh_from_db()
        self.assertEqual(self.page.media_items.count(), 0)  # live is untouched
        draft = self.page.get_latest_revision_as_object()
        items = list(draft.media_items.all())
        self.assertEqual(len(items), 5)
        self.assertEqual(items[0].group, "Historia")
        self.assertIn("&lt;script&gt;", items[0].description)
        self.assertEqual([i.sort_order for i in items], list(range(5)))
        revision = self.page.latest_revision_id
        self.run_import(True)
        self.page.refresh_from_db()
        self.assertEqual(self.page.latest_revision_id, revision)
        self.assertEqual(get_image_model().objects.count(), 1)
        self.assertEqual(get_document_model().objects.count(), 3)
        self.page.get_latest_revision().publish()
        self.run_import(True)
        self.assertEqual(self.page.media_items.count(), 5)

    def test_missing_and_corrupt_files_write_nothing(self):
        (self.bundle / "files/2.pdf").write_bytes(b"changed")
        with self.assertRaises(CommandError):
            self.run_import(True)
        self.assertEqual(get_image_model().objects.count(), 0)
        self.assertEqual(get_document_model().objects.count(), 0)

    def test_path_escape_rejected(self):
        path = self.bundle / "manifest.json"
        data = json.loads(path.read_text())
        data["items"][0]["path"] = "../media/test.png"
        path.write_text(json.dumps(data))
        with self.assertRaises(CommandError):
            self.run_import(True)

    def test_storage_cleanup_on_revision_failure(self):
        with patch.object(SpecialCallsignPage, "save_revision", side_effect=RuntimeError("failure")):
            with self.assertRaises(CommandError):
                self.run_import(True)
        self.assertEqual(get_image_model().objects.count(), 0)
        self.assertEqual(get_document_model().objects.count(), 0)
        self.assertFalse(any(p.is_file() for p in (self.root / "wagtail").rglob("*")))
