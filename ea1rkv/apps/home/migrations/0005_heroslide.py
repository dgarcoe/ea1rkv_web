from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0004_club_description"),
        ("wagtailimages", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HeroSlide",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.IntegerField(blank=True, editable=False, null=True)),
                ("credit", models.CharField(blank=True, max_length=300, verbose_name="Autor, fuente y licencia")),
                ("image", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="wagtailimages.image", verbose_name="Fotografía")),
                ("page", modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name="hero_slides", to="home.homepage")),
            ],
            options={"ordering": ["sort_order"], "abstract": False},
        ),
    ]
