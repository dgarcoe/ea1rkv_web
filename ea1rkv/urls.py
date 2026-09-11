"""URL configuration for EA1RKV Radioclub website."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls

from ea1rkv.apps.base.sitemaps import MultilingualSitemap
from ea1rkv.apps.base.views import robots_txt
from ea1rkv.apps.blog.feeds import BlogFeed
from ea1rkv.apps.search.views import search

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("django-admin/", admin.site.urls),
    path("feed/", BlogFeed(), name="blog_feed"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"pages": MultilingualSitemap}},
        name="sitemap",
    ),
]

urlpatterns += i18n_patterns(
    path("search/", search, name="search"),
    path("", include(wagtail_urls)),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
