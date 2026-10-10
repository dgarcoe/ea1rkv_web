from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("club", "0005_services_content")]
    operations = [migrations.AddField(
        model_name="callsignmedia", name="source_key",
        field=models.CharField(max_length=200, blank=True, editable=False),
    )]
