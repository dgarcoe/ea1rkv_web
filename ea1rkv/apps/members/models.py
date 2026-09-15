"""Member models for EA1RKV radioclub members directory."""

import uuid

from django import forms
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index

from .private import PrivateStorage, private_upload


class MemberIndexPage(Page):
    """Directory listing of club members."""

    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel("members", label="Members"),
    ]

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Members Directory"

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
    ]


class ClubDocumentsPage(Page):
    intro = RichTextField("Introducción", blank=True)
    privacy_notice = RichTextField(
        "Información sobre el uso del correo",
        blank=True,
        default=(
            "<p>Guardaremos tu correo para registrar el acceso a la documentación "
            "del club. Puedes solicitar su consulta o eliminación contactando con "
            "el radioclub.</p>"
        ),
    )
    parent_page_types = ["home.HomePage"]
    subpage_types = []
    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("privacy_notice"),
        InlinePanel(
            "private_documents", label="Documento", heading="Documentación privada"
        ),
    ]
    search_fields = []

    class Meta:
        verbose_name = "Documentación para socios"

    def serve(self, request, *args, **kwargs):
        from .views import documents_page

        return documents_page(request, self)


class ClubDocument(Orderable):
    download_key = models.UUIDField(default=uuid.uuid4, editable=False)
    page = ParentalKey(
        ClubDocumentsPage, related_name="private_documents", on_delete=models.CASCADE
    )
    title = models.CharField("Título", max_length=200)
    category = models.CharField("Categoría", max_length=100, default="Actas")
    date = models.DateField("Fecha")
    description = models.TextField("Descripción", blank=True)
    file = models.FileField(
        "Archivo privado", storage=PrivateStorage(), upload_to=private_upload
    )
    panels = [
        FieldPanel(name) for name in ("title", "category", "date", "description")
    ] + [FieldPanel("file", widget=forms.FileInput)]


class MemberDownloadEmail(models.Model):
    """Email supplied by a member before downloading private documentation."""

    email = models.EmailField("Correo electrónico", unique=True)
    confirmed_member = models.BooleanField("Confirmó ser socio", default=True)
    first_download_at = models.DateTimeField("Primera descarga", auto_now_add=True)
    last_download_at = models.DateTimeField("Última descarga", auto_now=True)
    download_count = models.PositiveIntegerField("Número de descargas", default=0)
    last_document = models.CharField("Último documento", max_length=200, blank=True)

    class Meta:
        verbose_name = "Correo de descarga"
        verbose_name_plural = "Correos de descargas"
        ordering = ["-last_download_at"]

    def __str__(self):
        return self.email


class Member(Orderable):
    """An individual radioclub member."""

    page = ParentalKey(
        MemberIndexPage,
        on_delete=models.CASCADE,
        related_name="members",
    )
    callsign = models.CharField(max_length=20, help_text="Amateur radio callsign")
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True, help_text="Short biography")
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    qrz_url = models.URLField(blank=True, help_text="QRZ.com profile URL")
    is_board_member = models.BooleanField(
        default=False,
        help_text="Is this member part of the board of directors?",
    )
    role = models.CharField(
        max_length=100,
        blank=True,
        help_text="Role in the club (e.g., President, Secretary)",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("callsign"),
                FieldPanel("name"),
                FieldPanel("role"),
                FieldPanel("is_board_member"),
            ],
            heading="Member Details",
        ),
        FieldPanel("photo"),
        FieldPanel("bio"),
        FieldPanel("qrz_url"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Member"

    def __str__(self):
        return f"{self.callsign} - {self.name}"
