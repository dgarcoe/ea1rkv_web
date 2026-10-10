from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET


@require_GET
@cache_page(60 * 60)
def robots_txt(request):
    sitemap = request.build_absolute_uri(reverse("sitemap"))
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /django-admin/",
            "Disallow: /search/",
            "Disallow: /gl/search/",
            "Disallow: /en/search/",
            f"Sitemap: {sitemap}",
            "",
        ]
    )
    return HttpResponse(content, content_type="text/plain; charset=utf-8")
