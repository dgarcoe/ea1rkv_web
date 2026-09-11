from collections import OrderedDict
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.utils.translation import gettext as _, gettext_noop
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


FEATURES = ["h2", "h3", "bold", "italic", "ol", "ul", "link", "document-link", "image", "embed"]


class ServicesPage(Page):
    intro = RichTextField("Presentación", blank=True, features=FEATURES)
    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel("frequencies", label="Frecuencia", heading="Tabla de frecuencias"),
        InlinePanel("service_cards", label="Servicio", heading="Servicios y accesos remotos"),
    ]
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
        context["has_service_groups"] = any(
            entries for _, entries in context["service_groups"]
        )
        return context


class FrequencyEntry(Orderable):
    page = ParentalKey(ServicesPage, related_name="frequencies", on_delete=models.CASCADE)
    name = models.CharField("Nombre / servicio", max_length=160)
    callsign = models.CharField("Indicativo", max_length=40, blank=True)
    frequency = models.CharField("Frecuencia", max_length=80)
    mode = models.CharField("Modo / tono", max_length=100, blank=True)
    status = models.CharField("Estado", max_length=120, blank=True)
    notes = models.CharField("Notas", max_length=300, blank=True)
    panels = [FieldPanel("name"), FieldPanel("callsign"), FieldPanel("frequency"), FieldPanel("mode"), FieldPanel("status"), FieldPanel("notes")]

    class Meta(Orderable.Meta):
        verbose_name = "Frecuencia"
        verbose_name_plural = "Frecuencias"


class ClubService(Orderable):
    ICONS = [("qsl", "QSL"), ("aprs", "APRS"), ("echolink", "Echolink"), ("remote", "Acceso remoto"), ("training", "Formación"), ("contest", "Concursos"), ("other", "Otros")]
    page = ParentalKey(ServicesPage, related_name="service_cards", on_delete=models.CASCADE)
    title = models.CharField("Nombre del servicio", max_length=160)
    icon = models.CharField("Icono", max_length=20, choices=ICONS, default="other")
    description = RichTextField("Descripción", blank=True, features=FEATURES)
    remote_address = models.CharField("Dirección / remoto", max_length=200, blank=True)
    remote_port = models.CharField("Puerto / canal", max_length=80, blank=True)
    link_url = models.URLField("Enlace", blank=True)
    link_label = models.CharField("Texto del enlace", max_length=80, blank=True)
    status = models.CharField("Estado", max_length=120, blank=True)
    panels = [FieldPanel("title"), FieldPanel("icon"), FieldPanel("description"), MultiFieldPanel([FieldPanel("remote_address"), FieldPanel("remote_port"), FieldPanel("status")], heading="Acceso remoto"), MultiFieldPanel([FieldPanel("link_url"), FieldPanel("link_label")], heading="Enlace opcional")]

    class Meta(Orderable.Meta):
        verbose_name = "Servicio del radioclub"
        verbose_name_plural = "Servicios del radioclub"


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
    LAYOUTS = [("activity", "Actividad: información primero"),
               ("award", "Diploma: bases primero"), ("report", "Reportaje: fotografías primero")]
    layout = models.CharField("Plantilla de presentación", max_length=20, choices=LAYOUTS, default="activity",
                              help_text="Elige un diseño ya preparado. Puedes cambiarlo sin perder contenido.")
    callsign = models.CharField("Indicativo", max_length=30)
    summary = models.CharField("Resumen de la actividad", max_length=300, blank=True)
    content = RichTextField("Información de la actividad y QSL", blank=True, features=FEATURES)
    start_date = models.DateField("Fecha de inicio", null=True, blank=True)
    end_date = models.DateField("Fecha de fin", null=True, blank=True)
    qrz_url = models.URLField("Página en QRZ", blank=True)
    location = models.CharField("Lugar / locator", max_length=200, blank=True)
    bands = models.CharField("Bandas", max_length=200, blank=True)
    modes = models.CharField("Modos", max_length=200, blank=True)
    schedule = models.CharField("Horario y zona horaria", max_length=200, blank=True,
                                help_text="Indica si los horarios son UTC o locales.")
    qsl_information = RichTextField("Cómo solicitar la QSL", blank=True, features=FEATURES)
    award_rules = RichTextField("Bases del diploma", blank=True, features=FEATURES)
    cover_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+", verbose_name="Portada / diploma")
    content_panels = Page.content_panels + [
        FieldPanel("layout"), FieldPanel("callsign"), FieldPanel("summary"), FieldPanel("cover_image"),
        MultiFieldPanel([FieldPanel(name) for name in
                         ("start_date", "end_date", "location", "bands", "modes", "schedule", "qrz_url")], heading="Ficha de la actividad"),
        FieldPanel("content", heading="Presentación / crónica"),
        FieldPanel("qsl_information"), FieldPanel("award_rules"),
        InlinePanel("media_items", label="Contenido", heading="Biblioteca del indicativo"),
    ]
    parent_page_types = ["club.CallsignsPage"]
    subpage_types = []
    search_fields = Page.search_fields + [index.SearchField(name) for name in
                                         ("callsign", "summary", "content", "qsl_information", "award_rules")]

    @property
    def activity_details(self):
        return [(label, getattr(self, name)) for name, label in
                [("location", _("Lugar / locator")), ("bands", _("Bandas")),
                 ("modes", _("Modos")), ("schedule", _("Horario"))]
                if getattr(self, name)]

    class Meta:
        verbose_name = "Indicativo especial"

    def clean(self):
        super().clean()
        self.callsign = self.callsign.strip().upper()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "La fecha de fin no puede ser anterior a la de inicio."})

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        items = list(self.media_items.select_related("image", "asset").all())
        selected_type = request.GET.get("tipo", "")
        if selected_type not in dict(CallsignMedia.TYPES):
            selected_type = ""
        selected_group = request.GET.get("grupo", "")
        group_names = list(dict.fromkeys(item.group for item in items if item.group))
        filtered = [item for item in items if
                    (not selected_type or item.kind == selected_type) and
                    (not selected_group or item.group == selected_group)]
        entries = Paginator(filtered, 12).get_page(request.GET.get("biblioteca_pagina"))
        groups = OrderedDict()
        for item in entries:
            groups.setdefault(item.group or _("Material de la actividad"), []).append(item)
        context.update({
            "library_types": CallsignMedia.TYPES, "library_type": selected_type,
            "library_group": selected_group, "library_group_names": group_names,
            "library_groups": groups.items(), "library_entries": entries,
            "library_total": len(items), "library_count": len(filtered),
            "library_query": urlencode({"tipo": selected_type, "grupo": selected_group}),
        })
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


class CallsignDownload(Orderable):
    page = ParentalKey(SpecialCallsignPage, related_name="downloads", on_delete=models.CASCADE)
    document = models.ForeignKey("wagtaildocs.Document", on_delete=models.CASCADE,
                                 related_name="+", verbose_name="Documento")
    description = models.CharField("Descripción", max_length=300, blank=True)
    panels = [FieldPanel("document"), FieldPanel("description")]

    class Meta(Orderable.Meta):
        verbose_name = "Documento del indicativo"


def youtube_video_id(url):
    """Accept individual YouTube videos, never arbitrary iframe URLs."""
    try:
        parts = urlsplit(url.strip())
        if parts.scheme not in ("http", "https") or parts.username or parts.password:
            return ""
        if parts.port not in (None, 80, 443):
            return ""
        host = (parts.hostname or "").lower()
        path = parts.path.strip("/").split("/")
        if host in ("youtu.be", "www.youtu.be") and len(path) == 1:
            video_id = path[0]
        elif host in ("youtube.com", "www.youtube.com", "m.youtube.com", "www.youtube-nocookie.com"):
            if parts.path == "/watch":
                video_id = parse_qs(parts.query).get("v", [""])[0]
            elif len(path) == 2 and path[0] in ("embed", "shorts", "live"):
                video_id = path[1]
            else:
                return ""
        else:
            return ""
        return video_id if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) else ""
    except (ValueError, AttributeError):
        return ""


class CallsignMedia(Orderable):
    TYPES = [("document", gettext_noop("Documentos")), ("image", gettext_noop("Imágenes")), ("video", gettext_noop("Vídeos")),
             ("audio", gettext_noop("Audio")), ("youtube", gettext_noop("YouTube"))]
    VIDEO_EXTENSIONS = {"mp4", "webm", "m4v"}
    AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "flac"}
    page = ParentalKey(SpecialCallsignPage, related_name="media_items", on_delete=models.CASCADE)
    kind = models.CharField("Tipo de contenido", max_length=20, choices=TYPES, default="image")
    title = models.CharField("Título", max_length=255)
    description = RichTextField("Descripción", blank=True, features=FEATURES,
                                help_text="Se muestra siempre junto al contenido, sin abrir desplegables.")
    group = models.CharField("Grupo / álbum", max_length=100, blank=True,
                             help_text="Usa el mismo nombre para agrupar varios elementos.")
    credit = models.CharField("Autor / créditos", max_length=300, blank=True)
    image = models.ForeignKey("wagtailimages.Image", null=True, blank=True,
                              on_delete=models.PROTECT, related_name="+", verbose_name="Imagen")
    asset = models.ForeignKey("wagtaildocs.Document", null=True, blank=True,
                              on_delete=models.PROTECT, related_name="+",
                              verbose_name="Archivo (documento, vídeo o audio)",
                              help_text="Sube o elige el archivo. Vídeo: MP4, WebM o M4V. Audio: MP3, WAV, OGG, M4A o FLAC.")
    youtube_url = models.URLField("Enlace de YouTube", blank=True,
                                  help_text="Pega el enlace al vídeo, no el código de inserción.")
    panels = [FieldPanel("kind"), FieldPanel("title"), FieldPanel("description"),
              FieldPanel("group"), FieldPanel("credit"),
              MultiFieldPanel([FieldPanel("image"), FieldPanel("asset"), FieldPanel("youtube_url")],
                              heading="Contenido (completa solo el campo correspondiente al tipo)")]

    class Meta(Orderable.Meta):
        verbose_name = "Contenido de la biblioteca"
        verbose_name_plural = "Contenidos de la biblioteca"

    @property
    def youtube_embed_url(self):
        video_id = youtube_video_id(self.youtube_url)
        return f"https://www.youtube-nocookie.com/embed/{video_id}" if video_id else ""

    def clean(self):
        super().clean()
        self.group = self.group.strip()
        self.youtube_url = self.youtube_url.strip()
        required = {"image": "image", "document": "asset", "video": "asset",
                    "audio": "asset", "youtube": "youtube_url"}.get(self.kind)
        errors = {}
        values = {"image": self.image_id, "asset": self.asset_id, "youtube_url": self.youtube_url}
        if required and not values[required]:
            errors[required] = "Añade el contenido correspondiente al tipo seleccionado."
        for field, value in values.items():
            if value and field != required:
                errors[field] = "Deja este campo vacío para el tipo seleccionado."
        if self.kind == "youtube" and self.youtube_url and not youtube_video_id(self.youtube_url):
            errors["youtube_url"] = "Introduce un enlace válido a un vídeo de YouTube."
        if self.asset_id and self.kind in ("video", "audio"):
            extensions = self.VIDEO_EXTENSIONS if self.kind == "video" else self.AUDIO_EXTENSIONS
            if self.asset.file_extension.lower() not in extensions:
                errors["asset"] = "El formato no corresponde al tipo seleccionado: " + ", ".join(sorted(extensions)) + "."
        if errors:
            raise ValidationError(errors)
