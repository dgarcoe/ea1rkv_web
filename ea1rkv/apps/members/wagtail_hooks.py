from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import MemberDownloadEmail


class MemberDownloadEmailViewSet(SnippetViewSet):
    model = MemberDownloadEmail
    icon = "mail"
    menu_label = "Correos de descargas"
    menu_name = "member_download_emails"
    list_display = [
        "email",
        "first_download_at",
        "last_download_at",
        "download_count",
        "last_document",
    ]
    list_export = list_display
    export_filename = "correos-descargas-socios"
    search_fields = ["email", "last_document"]
    inspect_view_enabled = True
    add_view_enabled = False
    edit_view_enabled = False


register_snippet(MemberDownloadEmailViewSet)
