"""RSS feeds for the EA1RKV blog."""

from django.contrib.syndication.views import Feed

from ea1rkv.apps.blog.models import BlogPage


class BlogFeed(Feed):
    """RSS feed for the latest blog posts."""

    title = "EA1RKV - Vigo Val Miñor Radioclub"
    link = "/blog/"
    description = "Latest news and articles from EA1RKV Radioclub"

    def items(self):
        return BlogPage.objects.live().order_by("-date")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.intro

    def item_pubdate(self, item):
        return item.first_published_at

    def item_link(self, item):
        return item.full_url
