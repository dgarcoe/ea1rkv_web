from io import StringIO
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, Client
from .models import BlogIndexPage, BlogPage, BlogComment


class CommentTests(TestCase):
    def setUp(self):
        cache.clear()
        call_command("setup_radioclub", stdout=StringIO())
        self.page = BlogIndexPage.objects.first().add_child(instance=BlogPage(
            title="Test", slug="comments-test", intro="Intro", body=[], comments_enabled=True))
        self.page.save_revision().publish()
        self.data = {"name": "EA1TEST", "text": "Hello <script>alert(1)</script>", "consent": "on"}

    def test_pending_hidden_approved_escaped(self):
        self.assertEqual(self.client.post(self.page.url, self.data).status_code, 302)
        comment = BlogComment.objects.get()
        self.assertEqual(comment.status, "pending")
        self.assertNotContains(self.client.get(self.page.url), "EA1TEST")
        comment.status = "approved"
        comment.save()
        response = self.client.get(self.page.url)
        self.assertContains(response, "EA1TEST")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_closed_and_csrf(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.page.url, self.data).status_code, 403)
        self.page.comments_enabled = False
        self.page.save_revision().publish()
        self.assertEqual(self.client.post(self.page.url, self.data).status_code, 403)
        self.assertFalse(BlogComment.objects.exists())

    def test_spam_validation_and_rate_limit(self):
        self.client.post(self.page.url, {**self.data, "website": "spam"})
        self.assertFalse(BlogComment.objects.exists())
        self.assertEqual(self.client.post(self.page.url, {**self.data, "consent": ""}).status_code, 400)
        self.client.post(self.page.url, self.data)
        self.assertEqual(self.client.post(self.page.url, self.data).status_code, 429)
        self.assertEqual(BlogComment.objects.count(), 1)
