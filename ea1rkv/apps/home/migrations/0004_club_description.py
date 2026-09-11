"""Replace only the original starter copy, preserving editorial changes."""
from django.db import migrations

OLD_DESCRIPTION = '<p>Somos la Unión de Radioafeccionados de Vigo-Val Miñor, con indicativo EA1RKV. Un punto de encuentro para quienes compartimos el interés por la radioafición.</p><p>En esta web podrás conocer el radioclub y seguir nuestro blog: noticias, experiencias y artículos sobre radio.</p>'
NEW_DESCRIPTION = '<p>Somos la Unión de Radioafeccionados de Vigo-Val Miñor, con indicativo <b>EA1RKV</b>. Un punto de encuentro para quienes compartimos la curiosidad por las ondas, la comunicación y la experimentación con la radio.</p><p>Queremos acercar la radioafición a nuestro entorno y crear un espacio para aprender, intercambiar conocimientos y compartir experiencias. Tanto si llevas años en las ondas como si estás empezando a descubrir este mundo, aquí tienes un lugar para conocerlo mejor.</p><p>En esta web encontrarás la presentación del radioclub y nuestro blog, donde compartiremos noticias, experiencias y artículos sobre radioafición desde Vigo y Val Miñor.</p>'


def forwards(apps, schema_editor):
    alias = schema_editor.connection.alias
    home = apps.get_model("home", "HomePage")
    home.objects.using(alias).filter(content=OLD_DESCRIPTION).update(content=NEW_DESCRIPTION)
    content_type = apps.get_model("contenttypes", "ContentType").objects.using(alias).filter(app_label="home", model="homepage").first()
    if content_type is None:
        return
    revisions = apps.get_model("wagtailcore", "Revision").objects.using(alias).filter(content_type_id=content_type.pk)
    for revision in revisions.iterator():
        if revision.content.get("content") == OLD_DESCRIPTION:
            content = revision.content.copy()
            content["content"] = NEW_DESCRIPTION
            revisions.filter(pk=revision.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [("home", "0003_convert_content")]
    operations = [migrations.RunPython(forwards)]
