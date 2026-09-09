# Editor clásico e indicativos especiales

## Actualizar una instalación existente

Desde la rama `codex/ea1rkv-inicio-blog`, descarga los últimos cambios y ejecuta:

```bash
git pull
python -m pip install -r requirements/base.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Reinicia el servidor y recarga el administrador sin caché. En Docker reconstruye
la imagen para instalar las nuevas dependencias antes de ejecutar las migraciones.
No borres la base de datos. La migración añade campos y conserva las páginas,
los borradores, las fotografías y el texto existentes.

## Escribir

Los campos de texto rico usan TinyMCE, con menú y barra de herramientas visibles:
títulos, negrita, cursiva, listas, enlaces, tablas y pantalla completa. Los botones
de imagen y documento abren la biblioteca de Wagtail. El editor se sirve desde
la propia web, sin cuenta ni clave de un servicio externo. Los recursos de TinyMCE
se distribuyen con `django-tinymce`; se utiliza su modalidad GPL.

Las imágenes y los enlaces internos existentes conservan las referencias a la
biblioteca. Los vídeos incrustados existentes se muestran como una etiqueta en
el editor y se conservan al guardar. El HTML pegado se limpia al guardar; no se
admiten scripts ni iframes arbitrarios.

## Crear un indicativo

En **Páginas → Inicio → Indicativos especiales → Añadir página**, elige
**Indicativo especial**. No hay que construir bloques. Completa la ficha:

- Plantilla: **Actividad**, **Diploma** o **Reportaje**.
- Indicativo, título, resumen e imagen de portada o diploma.
- Fechas, lugar/locator, bandas, modos, horario con zona horaria y enlace a QRZ.
- Presentación o crónica, instrucciones QSL y bases del diploma en texto rico.
- Fotografías con pie, autor y nombre de álbum; puedes ordenarlas.
- Documentos descargables, como bases o programas, con su descripción.

Actividad presenta primero el texto; Diploma destaca las bases antes del texto;
Reportaje coloca los álbumes antes de la crónica. Puedes cambiar la plantilla sin
reescribir ni perder los campos. Los apartados vacíos no aparecen en la web.
Usa **Vista previa**, guarda un borrador o publica con los controles habituales.

La organización por indicativo y álbum sigue la referencia del repositorio
`special_callsign_media_sharing_web`. Esta versión gestiona la información, las
fotografías y los documentos dentro de Wagtail; no conecta con la base de datos
externa de aquella aplicación ni replica su subida pública o descarga ZIP.
