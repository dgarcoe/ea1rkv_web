"""Template tags for blog functionality."""

from django import template

from ea1rkv.apps.blog.models import BlogCategory, BlogPage

register = template.Library()


@register.inclusion_tag("blog/includes/latest_posts.html", takes_context=True)
def latest_posts(context, count=3):
    """Render the latest blog posts."""
    return {
        "posts": BlogPage.objects.live().order_by("-date")[:count],
        "request": context["request"],
    }


@register.inclusion_tag("blog/includes/category_list.html")
def blog_categories():
    """Render the list of blog categories."""
    return {"categories": BlogCategory.objects.all()}
