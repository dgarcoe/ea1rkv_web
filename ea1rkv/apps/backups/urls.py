from django.urls import path

from . import views

app_name = "admin_backups"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create, name="create"),
    path("download/<str:name>/", views.download, name="download"),
    path("restore/", views.restore, name="restore"),
]
