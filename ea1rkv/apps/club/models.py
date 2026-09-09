from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


FEATURES = ["h2", "h3", "bold", "italic", "ol", "ul", "link", "document-link", "image", "embed"]


class ServicesPage(Page):
    intro = RichTextField("Presentación", blank=True, features=FEATURES)
    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["club.ServicePage"]
    max_count_per_parent = 1

    class Meta:
        verbose_name = "Servicios del radioclub"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        entries = ServicePage.objects.child_of(self).live().public().order_by("path")
        context["service_groups"] = [
            (label, [entry for entry in entries if entry.kind == value])
            for value, label in ServicePage.KINDS
        ]
        return context


class ServicePage(Page):
    KINDS = [("repeater", "Repetidores"), ("frequency", "Frecuencias"),
             ("equipment", "Equipos de radio"), ("other", "Otros servicios")]
    kind = models.CharField("Tipo", max_length=20, choices=KINDS, default="repeater")
    summary = models.CharField("Resumen", max_length=300, blank=True)
    content = RichTextField("Descripción y condiciones de uso", blank=True, features=FEATURES)
    frequency = models.CharField("Frecuencia / salida del repetidor (MHz)", max_length=80, blank=True)
    input_frequency = models.CharField("Entrada del repetidor (MHz)", max_length=80, blank=True)
    mode = models.CharField("Modo", max_length=80, blank=True)
    access = models.CharField("Tono o parámetros de acceso", max_length=150, blank=True)
    location = models.CharField("Ubicación / cobertura", max_length=200, blank=True)
    equipment = models.CharField("Modelo de equipo", max_length=150, blank=True)
    availability = models.CharField("Estado / disponibilidad", max_length=150, blank=True)
    photo = models.ForeignKey("wagtailimages.Image", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+", verbose_name="Fotografía")
    content_panels = Page.content_panels + [
        FieldPanel("kind"), FieldPanel("summary"), FieldPanel("content"), FieldPanel("photo"),
        MultiFieldPanel([FieldPanel(name) for name in
                         ("frequency", "input_frequency", "mode", "access", "location", "equipment", "availability")],
                        heading="Datos técnicos (completa solo los que correspondan)"),
    ]
    parent_page_types = ["club.ServicesPage"]
    subpage_types = []
    search_fields = Page.search_fields + [index.SearchField("summary"), index.SearchField("content")]

    class Meta:
        verbose_name = "Servicio / recurso"

    @property
    def technical_details(self):
        return [(label, getattr(self, field)) for field, label in [
            ("frequency", "Frecuencia / salida (MHz)"), ("input_frequency", "Entrada (MHz)"),
            ("mode", "Modo"), ("access", "Acceso"), ("location", "Ubicación / cobertura"),
            ("equipment", "Equipo"), ("availability", "Estado / disponibilidad")
        ] if getattr(self, field)]


class CallsignsPage(Page):
    intro = RichTextField("Presentación", blank=True, features=FEATURES)
    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["club.SpecialCallsignPage"]
    max_count_per_parent = 1

    class Meta:
        verbose_name = "Indicativos especiales"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        entries = SpecialCallsignPage.objects.child_of(self).live().public().select_related("cover_image").order_by("-start_date", "-pk")
        context["callsigns"] = Paginator(entries, 12).get_page(request.GET.get("page"))
        return context


class SpecialCallsignPage(Page):
    callsign = models.CharField("Indicativo", max_length=30)
    summary = models.CharField("Resumen de la actividad", max_length=300, blank=True)
    content = RichTextField("Información de la actividad y QSL", blank=True, features=FEATURES)
    start_date = models.DateField("Fecha de inicio", null=True, blank=True)
    end_date = models.DateField("Fecha de fin", null=True, blank=True)
    qrz_url = models.URLField("Página en QRZ", blank=True)
    cover_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+", verbose_name="Portada / diploma")
    content_panels = Page.content_panels + [
        FieldPanel("callsign"), FieldPanel("summary"), FieldPanel("cover_image"),
        MultiFieldPanel([FieldPanel("start_date"), FieldPanel("end_date"), FieldPanel("qrz_url")], heading="Datos de la actividad"),
        FieldPanel("content"), InlinePanel("photos", label="Fotografías", heading="Álbum de fotos"),
    ]
    parent_page_types = ["club.CallsignsPage"]
    subpage_types = []
    search_fields = Page.search_fields + [index.SearchField("callsign"), index.SearchField("summary"), index.SearchField("content")]

    class Meta:
        verbose_name = "Indicativo especial"

    def clean(self):
        super().clean()
        self.callsign = self.callsign.strip().upper()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "La fecha de fin no puede ser anterior a la de inicio."})

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        groups = OrderedDict()
        for photo in self.photos.select_related("image").all():
            groups.setdefault(photo.group.strip() or "Fotografías", []).append(photo)
        context["photo_groups"] = groups.items()
        return context


class CallsignPhoto(Orderable):
    page = ParentalKey(SpecialCallsignPage, related_name="photos", on_delete=models.CASCADE)
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+", verbose_name="Imagen")
    caption = models.CharField("Pie de foto", max_length=300, blank=True)
    credit = models.CharField("Autor / créditos", max_length=300, blank=True)
    group = models.CharField("Álbum o grupo (opcional)", max_length=100, blank=True,
                             help_text="Las fotos con el mismo nombre se muestran juntas.")
    panels = [FieldPanel("image"), FieldPanel("caption"), FieldPanel("credit"), FieldPanel("group")]

    class Meta(Orderable.Meta):
        verbose_name = "Fotografía del indicativo"
