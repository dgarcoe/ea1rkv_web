from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.fields


class Migration(migrations.Migration):
    dependencies = [("club", "0004_populate_media_library")]
    operations = [
        migrations.CreateModel(
            name="FrequencyEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.IntegerField(blank=True, editable=False, null=True)),
                ("name", models.CharField(max_length=160, verbose_name="Nombre / servicio")),
                ("callsign", models.CharField(blank=True, max_length=40, verbose_name="Indicativo")),
                ("frequency", models.CharField(max_length=80, verbose_name="Frecuencia")),
                ("mode", models.CharField(blank=True, max_length=100, verbose_name="Modo / tono")),
                ("status", models.CharField(blank=True, max_length=120, verbose_name="Estado")),
                ("notes", models.CharField(blank=True, max_length=300, verbose_name="Notas")),
                ("page", modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name="frequencies", to="club.servicespage")),
            ],
            options={"verbose_name": "Frecuencia", "verbose_name_plural": "Frecuencias", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="ClubService",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.IntegerField(blank=True, editable=False, null=True)),
                ("title", models.CharField(max_length=160, verbose_name="Nombre del servicio")),
                ("icon", models.CharField(choices=[("qsl", "QSL"), ("aprs", "APRS"), ("echolink", "Echolink"), ("remote", "Acceso remoto"), ("training", "Formación"), ("contest", "Concursos"), ("other", "Otros")], default="other", max_length=20, verbose_name="Icono")),
                ("description", wagtail.fields.RichTextField(blank=True, verbose_name="Descripción")),
                ("remote_address", models.CharField(blank=True, max_length=200, verbose_name="Dirección / remoto")),
                ("remote_port", models.CharField(blank=True, max_length=80, verbose_name="Puerto / canal")),
                ("link_url", models.URLField(blank=True, verbose_name="Enlace")),
                ("link_label", models.CharField(blank=True, max_length=80, verbose_name="Texto del enlace")),
                ("status", models.CharField(blank=True, max_length=120, verbose_name="Estado")),
                ("page", modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name="service_cards", to="club.servicespage")),
            ],
            options={"verbose_name": "Servicio del radioclub", "verbose_name_plural": "Servicios del radioclub", "ordering": ["sort_order"]},
        ),
    ]
