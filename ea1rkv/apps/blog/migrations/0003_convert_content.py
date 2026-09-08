from django.db import migrations
from ea1rkv.apps.base.migrations._richtext import migrate_content


def forwards(apps, schema_editor):
    migrate_content(apps, schema_editor, "blog", "BlogPage")


class Migration(migrations.Migration):
    dependencies = [("blog", "0002_blogpage_content")]
    operations = [migrations.RunPython(forwards)]
