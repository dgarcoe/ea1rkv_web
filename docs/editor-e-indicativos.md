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

## Cabecera rotatoria

En Páginas → Inicio → Cabecera → Cabecera rotatoria, añade fotografías y sus
créditos (autor, fuente y licencia). Reordénalas y publica la página.
La lista tiene prioridad sobre la imagen de cabecera individual, que se conserva
como alternativa cuando la lista está vacía. Una sola fotografía permanece fija.
Con varias, cambia cada seis segundos y ofrece Anterior, Pausar y Siguiente.
Se pausa con el ratón, el foco del teclado o la pestaña oculta; la preferencia
de movimiento reducido desactiva el avance automático inicialmente.
Sin JavaScript se muestra la primera imagen.

## Despliegue detrás de un Nginx existente

El archivo docker-compose.prod.external.yml levanta PostgreSQL, Redis, Wagtail
y un Nginx propio, conectado a ea1rfi-network. No publica puertos en el host.
El Nginx propio comparte los volúmenes de estáticos y multimedia en modo lectura.
El proxy público del otro Compose también debe pertenecer a ea1rfi-network.

En el servidor HTTPS de ea1rkv.com, conserva las rutas de Quendaward y MQTT
y usa este bloque para la web. No uses `location = /`: solo coincidiría con la raíz.

```nginx
location / {
    proxy_pass http://ea1rkv_nginx:80;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

No añadas volúmenes de Wagtail al proxy público ni reglas locales para /static/
o /media/. Configura client_max_body_size 200M en su servidor HTTPS si necesitas
subir archivos grandes; el límite público anterior de 15 MB sigue prevaleciendo
hasta cambiarlo. Las imágenes de Wagtail tienen además su límite de 10 MB.

Antes de actualizar, guarda una copia de PostgreSQL y del volumen multimedia.

```bash
git pull --ff-only
docker network inspect ea1rfi-network
docker compose -f docker-compose.prod.external.yml up -d --build web nginx
docker compose -f docker-compose.prod.external.yml logs --tail=100 web
docker compose -f docker-compose.prod.external.yml exec nginx nginx -t
```

Si la red no existe, créala con docker network create ea1rfi-network.
El arranque prepara los directorios raíz de los volúmenes como root y baja
a app antes de migrar, inicializar páginas, recopilar estáticos y ejecutar Gunicorn.
No realiza un cambio recursivo de propietario de archivos en cada arranque.
Para un volumen antiguo con subdirectorios de otro propietario, la reparación
puntual es:

```bash
docker compose -f docker-compose.prod.external.yml exec --user root web chown -R app:app /app/media
```

No uses down -v: elimina los volúmenes. La migración de cabecera añade una tabla,
conserva la fotografía individual y no borra contenido.
Para crear el administrador usa createsuperuser dentro del servicio web.
El administrador está en /admin/, español en / y las rutas de otros idiomas
usan /gl/ y /en/; el selector está disponible y las traducciones editoriales se gestionan desde la acción Traducir. Consulta [Idiomas](idiomas.md).
