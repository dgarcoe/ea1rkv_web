from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import BlogComment


class BlogCommentViewSet(SnippetViewSet):
    model = BlogComment
    icon = "comment"
    menu_label = "Comentarios del blog"
    menu_name = "blog_comments"
    add_to_admin_menu = True
    list_display = ["name", "page", "created_at", "status"]
    list_filter = ["status"]
    search_fields = ["name", "text"]
    inspect_view_enabled = True
    add_view_enabled = False


register_snippet(BlogCommentViewSet)
