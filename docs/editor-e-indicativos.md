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
- Biblioteca con imágenes, documentos, vídeos, audio y enlaces de YouTube.

Actividad presenta primero el texto; Diploma destaca las bases antes del texto;
Reportaje coloca la biblioteca antes de la crónica. Puedes cambiar la plantilla sin
reescribir ni perder los campos. Los apartados de texto vacíos no aparecen en la web.
Usa **Vista previa**, guarda un borrador o publica con los controles habituales.

## Biblioteca multimedia

En la ficha del indicativo, ve a **Biblioteca del indicativo → Añadir contenido**.
Cada elemento tiene tipo, título, descripción con editor clásico, grupo/álbum
opcional y autor/créditos. La descripción aparece completa junto al elemento en
la web, también al filtrar. Puedes ordenar los elementos en el administrador.

Elige uno de los cinco tipos y completa su fuente:

| Tipo | Campo que debes completar | Presentación pública |
| --- | --- | --- |
| Documentos | Archivo, desde la biblioteca de documentos | Título, descripción y descarga |
| Imágenes | Imagen, desde la biblioteca de imágenes | Imagen ampliable, descripción y descarga |
| Vídeos | Archivo MP4, WebM o M4V | Reproductor, descripción y descarga |
| Audio | Archivo MP3, WAV, OGG, M4A o FLAC | Reproductor, descripción y descarga |
| YouTube | Enlace al vídeo | Vídeo incrustado, descripción y enlace a YouTube |

Para vídeo y audio, la biblioteca de documentos de Wagtail permite subir también
estos formatos. Para mayor compatibilidad entre navegadores utiliza MP4 con
H.264/AAC y MP3. La extensión por sí sola no garantiza que un navegador soporte
los códecs del archivo. No hay reproducción automática.

YouTube admite enlaces normales, cortos (`youtu.be`), Shorts y directos. Se
valida el identificador y se usa el reproductor de `youtube-nocookie.com`.
No hace falta una clave de API ni copiar código HTML.

El visitante puede combinar **Tipo de contenido** y **Grupo / álbum**, pulsar
**Filtrar** y volver con **Mostrar todo**. Los filtros permanecen al pasar de
página; se muestran hasta 12 elementos por página. Los enlaces de los filtros
se pueden compartir. Los grupos reúnen todos los elementos con el mismo nombre.

Las migraciones `club.0003` y `club.0004` incorporan automáticamente las fotos
y los documentos anteriores, con sus descripciones, grupos y créditos. También
convierten cada revisión antigua para preservar sus cambios propios. Las tablas
anteriores se conservan para recuperación, pero ya no se editan por separado.
No se copian ni se vuelven a subir los archivos. Los nuevos elementos siguen el
flujo habitual de borrador, vista previa y publicación de la página.

La organización por indicativo, grupo y tipo sigue la referencia de
`special_callsign_media_sharing_web`. Esta versión gestiona el contenido dentro
de Wagtail; no conecta con la base de datos externa de aquella aplicación ni
replica su subida pública o descarga ZIP.

El Nginx de producción admite peticiones de hasta 200 MB. Si hay otro proxy
delante, su límite también debe permitir el tamaño del archivo. Los vídeos y
audios se sirven mediante el endpoint de documentos de Wagtail para conservar
sus comprobaciones de acceso, no mediante enlaces directos a su almacenamiento.

## Despliegue detrás de un Nginx existente

El archivo `docker-compose.prod.external.yml` levanta PostgreSQL, Redis y
Wagtail sin crear otro Nginx. Todos los servicios se conectan a la red externa
`ea1rfi-network` y Wagtail se publica únicamente en `127.0.0.1:8001`.

```bash
docker network inspect ea1rfi-network >/dev/null 2>&1 || docker network create ea1rfi-network
docker compose -f docker-compose.prod.external.yml build
docker compose -f docker-compose.prod.external.yml up -d
docker compose -f docker-compose.prod.external.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.external.yml exec web python manage.py setup_radioclub
docker compose -f docker-compose.prod.external.yml exec web python manage.py collectstatic --noinput
```

El Nginx del otro Compose debe conectarse también a `ea1rfi-network` y enviar el
tráfico a `http://ea1rkv-web:8000`. Los nombres `ea1rkv-web`, `ea1rkv-db` y
`ea1rkv-redis` quedan fijados para que el DNS interno de Docker sea estable.
Configura `client_max_body_size 200M` en ese Nginx. El puerto 8000 solo está
disponible dentro de la red Docker.
