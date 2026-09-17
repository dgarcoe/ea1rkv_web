from functools import reduce
from operator import or_

from django.db.models import Q
from wagtail.contrib.sitemaps import Sitemap
from wagtail.models import Page
from ea1rkv.apps.members.models import ClubDocumentsPage


class MultilingualSitemap(Sitemap):
    """Include every translated version of the site's root page tree."""

    def items(self):
        root = self.get_wagtail_site().root_page
        roots = root.get_translations(inclusive=True).live().public()
        path_filter = reduce(
            or_, (Q(path__startswith=translated.path) for translated in roots)
        )
        return (
            Page.objects.filter(path_filter)
            .exclude(pk__in=ClubDocumentsPage.objects.values("pk"))
            .live()
            .public()
            .order_by("path")
            .defer_streamfields()
            .specific()
        )
