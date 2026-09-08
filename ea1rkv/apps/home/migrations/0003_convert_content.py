from django.db import migrations
from ea1rkv.apps.base.migrations._richtext import migrate_content


def forwards(apps, schema_editor):
    migrate_content(apps, schema_editor, "home", "HomePage")


class Migration(migrations.Migration):
    dependencies = [("home", "0002_homepage_content_homepage_hero_image_credit_and_more")]
    operations = [migrations.RunPython(forwards)]
