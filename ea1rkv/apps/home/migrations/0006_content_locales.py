from django.db import migrations


def create_locales(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    for code in ("es", "gl", "en"):
        Locale.objects.using(schema_editor.connection.alias).get_or_create(language_code=code)


class Migration(migrations.Migration):
    dependencies = [("home", "0005_heroslide")]
    operations = [migrations.RunPython(create_locales, migrations.RunPython.noop)]
