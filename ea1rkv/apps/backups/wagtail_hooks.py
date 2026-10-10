from django.urls import include, path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem


class SuperuserMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.is_superuser


@hooks.register("register_admin_urls")
def register_backup_urls():
    return [path("backups/", include("ea1rkv.apps.backups.urls"))]


@hooks.register("register_admin_menu_item")
def register_backup_menu_item():
    return SuperuserMenuItem(
        "Copias de seguridad",
        reverse("admin_backups:index"),
        icon_name="download",
        order=990,
    )
