"""Search view for the EA1RKV website."""

from django.shortcuts import render

from wagtail.models import Page


def search(request):
    """Full-text search across all live pages."""
    query = request.GET.get("query", "")
    results = []

    if query:
        results = Page.objects.live().search(query)

    return render(
        request,
        "search/search.html",
        {
            "query": query,
            "results": results,
        },
    )
