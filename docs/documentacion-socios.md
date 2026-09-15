# Documentación para socios

En el .env del servidor establece CLUB_DOCUMENTS_PASSWORD con una contraseña
larga, compartida exclusivamente con los socios. No la subas al repositorio.
Sin contraseña configurada, el acceso está cerrado. Cambiarla invalida los
accesos anteriores tras recrear el contenedor web.

Despliega con git pull --ff-only y docker compose -f docker-compose.prod.external.yml
up -d --build (conserva el overlay analytics si lo utilizas). El arranque crea
Documentación para socios bajo Inicio. En Wagtail abre esa página, añade
documentos, categoría (por ejemplo Actas), fecha, descripción y archivo, y publica.
Los socios usan /documentacion-socios/. Sólo administradores/editores con
permisos de edición pueden subir archivos desde Wagtail.

Los archivos se guardan en /app/privatefiles, en el volumen private_volume que
sólo monta web. Incluye este volumen y la base de datos en tus copias de seguridad.
Nunca enlaces actas subidas a la biblioteca pública de Documentos ni al campo
de texto: utiliza Archivo privado. Archivos previamente publicados deben
retirarse también de sus URL públicas y cachés.

Las descargas exigen la sesión autorizada y una página publicada, no usan
/media/ ni /documents/. Borradores no publicados no aparecen. Las respuestas
son no-cache y noindex. Los cambios de categoría/título se guardan por revisión.
Este acceso es provisional y compartido; no identifica a cada socio.
