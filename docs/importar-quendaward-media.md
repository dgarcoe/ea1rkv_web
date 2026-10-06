# Migrar una biblioteca de quendaward_media a Wagtail

Importa en bloque la biblioteca de **una página de indicativo especial existente**.
Conserva títulos, descripciones, tipos, grupos, orden de elementos y archivos;
los enlaces YouTube se mantienen como enlaces. No importa usuarios, contraseñas,
datos de contactos de radio ni la configuración de la aplicación antigua.
La descripción se convierte de texto a HTML seguro conservando los saltos de línea.
El ancho personalizado de los vídeos YouTube se sustituye por el diseño adaptable
de Wagtail. Los textos con Markdown se conservan como texto, sin interpretar Markdown.

El importador crea un **borrador**, incorporando también los cambios que ya hubiera
en el último borrador de la página. No publica automáticamente ni cambia sus
fechas, portada o descripción general. La copia de los archivos se registra en
Imágenes/Documentos de Wagtail aunque aún no se haya publicado el borrador.

## 1. Actualizar Wagtail

Desde el repositorio del VPS, usando la rama `codex/ea1rkv-inicio-blog`:

```bash
cd ~/ea1rkv_web
git pull --ff-only
docker compose -f docker-compose.prod.external.yml up -d --build
```

Si utilizas el compose adicional de estadísticas, incluye también
`-f docker-compose.analytics.yml`, como en tus despliegues habituales.
El arranque aplica la migración `club.0006`, necesaria para registrar el origen.
Guarda una copia de seguridad de Wagtail con la funcionalidad existente.

## 2. Identificar el indicativo en la aplicación antigua

El exportador está en este repositorio; no hace falta modificar ni reconstruir
la aplicación Streamlit. Estos comandos usan el contenedor `quendaward-media`
definido en su compose:

```bash
docker cp scripts/export_quendaward_media.py quendaward-media:/tmp/export_quendaward_media.py
docker exec quendaward-media python /tmp/export_quendaward_media.py --list
```

Aparecerá una lista como `7 EG1912T`. Usa **el número real de tu instalación**.
Este ID del origen es independiente del ID de la página de Wagtail.

## 3. Exportar archivos y descripciones

Sustituye `7` por el ID obtenido. Evita editar o borrar medios en la aplicación
antigua mientras exportas, para que la copia de metadatos y archivos sea coherente.
La lectura de SQLite es de sólo lectura y compatible con WAL.

```bash
docker exec quendaward-media python /tmp/export_quendaward_media.py --award-id 7 --output /tmp/eg1912t-export
docker cp quendaward-media:/tmp/eg1912t-export ./eg1912t-export
docker cp ./eg1912t-export ea1rkv_web:/tmp/eg1912t-export
```

El directorio contiene `manifest.json` y `files/`. Deben viajar juntos. No uses
el ZIP público de Streamlit: no contiene los metadatos ni los enlaces YouTube.
No hace falta mover ni renombrar los originales. El exportador lee las variables
`MEDIA_DB_PATH`, `MEDIA_DIR` y `QUENDAWARD_DB_PATH` del contenedor antiguo.

Si repites la exportación, elige un directorio nuevo, por ejemplo
`/tmp/eg1912t-export-2`, y cambia las rutas en los siguientes comandos. El
exportador no sobrescribe una exportación anterior. Mantén el valor de `--source`
(por defecto `quendaward_media`) para conservar la identidad del origen.

## 4. Previsualizar la importación

Abre la página del indicativo en Wagtail. Si la URL de edición es
`/admin/pages/42/edit/`, su ID es `42`. Sustituye ese número en los comandos.
Cierra cualquier edición abierta de esa página durante la importación.

```bash
docker exec -u app ea1rkv_web python manage.py import_quendaward_media /tmp/eg1912t-export --page-id 42
```

Muestra el origen, destino, títulos, tipos, grupos y cantidades. Comprueba todos
los archivos nuevos y sus hashes SHA-256, los enlaces y los formatos antes de
escribir. Sin `--apply` no crea archivos, objetos ni revisiones.
Si hay errores, corrígelos antes de continuar. AVI/MOV y otros formatos no admitidos
por el reproductor actual requieren conversión y una exportación actualizada;
el importador no transcodifica ni cambia silenciosamente el tipo de contenido.

## 5. Crear el borrador y publicar

```bash
docker exec -u app ea1rkv_web python manage.py import_quendaward_media /tmp/eg1912t-export --page-id 42 --apply
```

Vuelve al administrador, abre esa página, revisa su biblioteca y utiliza
**Publicar**. No es necesario volver a subir los archivos desde el editor.
El comando no publica ni replica por sí mismo el contenido en otras traducciones.
Si necesitas importarlo también en otra página traducida, usa su propio ID y
revisa el borrador de ese idioma antes de publicarlo.

## Repetición, errores y límites

- Cada elemento lleva un identificador `origen:indicativo:elemento` en el borrador
  y en las revisiones publicadas. Repetir el comando sobre la misma página omite
  esos elementos: no duplica ni sobrescribe las descripciones editadas en Wagtail.
- Añade los nuevos elementos al final; no borra ni reordena los ya existentes.
- Los elementos que habías subido manualmente no llevan ese identificador y no
  se reconocen automáticamente. Revisa esos posibles duplicados en el borrador.
- Se validan todos los elementos nuevos antes de importar. Un error aborta el
  conjunto; si falla al guardar, se revierte la transacción y se intenta limpiar
  los archivos nuevos. El comando avisa si no consigue limpiar alguno.
- Las páginas bloqueadas o con un flujo de revisión activo no se modifican.
- El registro de importación pertenece al borrador: si lo descartas o restauras
  una revisión anterior a la importación, esos identificadores dejan de estar
  presentes. Importar después de ese descarte puede crear nuevos archivos.
- Conserva la exportación fuera del repositorio y guarda el informe de consola
  si hay errores. La aplicación antigua sigue disponible tras la migración.

Implementado para el esquema de `special_callsign_media_sharing_web`, rama
`claude/fix-youtube-description-style-lYxVS`, commit `71778d5`.
