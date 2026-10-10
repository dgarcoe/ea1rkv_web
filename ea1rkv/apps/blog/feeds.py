"""RSS feeds for the EA1RKV blog."""

from django.contrib.syndication.views import Feed

from wagtail.models import Site

from ea1rkv.apps.blog.models import BlogIndexPage, BlogPage


class BlogFeed(Feed):
    """RSS feed for the latest blog posts."""

    title = "EA1RKV - Vigo Val Miñor Radioclub"
    description = "Noticias y artículos del radioclub EA1RKV"

    def get_object(self, request):
        return Site.find_for_request(request)

    def link(self, site):
        blog = BlogIndexPage.objects.child_of(site.root_page).live().public().first()
        return blog.full_url if blog else site.root_page.full_url

    def items(self, site):
        return (BlogPage.objects.descendant_of(site.root_page).live().public()
                .order_by("-date", "-pk")[:20])

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.intro

    def item_pubdate(self, item):
        return item.first_published_at

    def item_link(self, item):
        return item.full_url

