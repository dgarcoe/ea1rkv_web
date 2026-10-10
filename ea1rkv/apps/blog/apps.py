from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = "ea1rkv.apps.blog"

    def ready(self):
        from . import telegram  # noqa: F401
