# Anuncios del blog en Telegram

La integración está desactivada por defecto. Necesitas un canal y un bot creado
con @BotFather. Añade el bot como administrador del canal con permiso para publicar.
No compartas el token ni lo guardes en GitHub.

## Activación en producción

Desde `~/ea1rkv_web`, actualiza la rama y edita `.env`:

```sh
git pull --ff-only
nano .env
```

Añade (sustituye los valores):

```dotenv
TELEGRAM_ENABLED=True
TELEGRAM_BOT_TOKEN=TOKEN_DEL_BOT
TELEGRAM_CHAT_ID=@nombre_del_canal
```

Para un canal privado usa su ID numérico, normalmente `-100…`, no su enlace de
invitación. El bot debe pertenecer al canal. En Wagtail, Configuración → Sitios,
comprueba el dominio `ea1rkv.com` y puerto `443`: los enlaces deben ser HTTPS.

```sh
docker compose -f docker-compose.prod.external.yml -f docker-compose.telegram.yml up -d --build
```

Si utilizas GoAccess, conserva también su fichero:

```sh
docker compose -f docker-compose.prod.external.yml -f docker-compose.analytics.yml -f docker-compose.telegram.yml up -d --build
```

El servicio `web` aplica las migraciones y `telegram` empieza cuando la web está
sana. El worker usa la misma base de datos y volumen de imágenes; consulta la cola
cada 15 segundos. No necesita un nuevo puerto ni cambios en nginx.
Incluye los mismos ficheros Compose en futuros despliegues.

## Publicar

En una entrada nueva en español, marca **Anunciar en Telegram** antes de su primera
publicación. Guardar un borrador no envía nada. Se anuncia al publicarse realmente,
también si lo publica el programador de Wagtail (que debe estar configurado).

El mensaje incluye título, resumen, botón para leer la entrada y, cuando existe,
la imagen de cabecera. Telegram debe poder descargar esa imagen por HTTPS.
Las entradas privadas, gallegas e inglesas no generan anuncios. Las actualizaciones
y las entradas ya publicadas antes de activar la integración tampoco. El checkbox
está desmarcado por defecto y se elige por entrada.

Antes de enviar, el worker vuelve a comprobar que la entrada sigue publicada,
pública y con la casilla marcada. Envía el contenido publicado más reciente.
Un anuncio ya enviado no se modifica ni se borra al editar o retirar la entrada.

## Estado y problemas

```sh
docker exec -u app ea1rkv_web python manage.py telegram_worker --status
docker compose -f docker-compose.prod.external.yml -f docker-compose.telegram.yml logs --tail=50 telegram
```

Estados: `pending` en cola; `sending` en proceso; `sent` confirmado (con ID de
mensaje); `failed` rechazado; `uncertain` sin confirmación; `cancelled` retirado.
Los límites temporales 429 de Telegram se reintentan hasta cinco veces, respetando
la espera indicada. Otros errores requieren revisión. Comprueba token, permisos,
canal, URL pública e imagen según corresponda.

Si un envío queda `uncertain`, mira primero el canal: una desconexión puede ocurrir
después de que Telegram haya publicado. No hay garantía de entrega exactamente una
vez en esa situación. El worker no reenvía automáticamente para evitar duplicados.
Sólo si no aparece el mensaje, reencola el ID mostrado por `--status`:

```sh
docker exec -u app ea1rkv_web python manage.py telegram_worker --retry 12
```

Ese comando sólo reencola; el worker hace el envío. Los envíos confirmados no pueden
reintentarse. No cambies el canal mientras haya envíos pendientes: cada registro
conserva su destino original. No actives este servicio en copias de pruebas.

Para restaurar una copia de seguridad, detén antes el servicio `telegram`. Antes
de volver a activarlo, revisa la cola restaurada frente a los mensajes del canal:
una copia antigua podría contener anuncios pendientes que ya se enviaron después.
Para desactivar nuevos anuncios y procesado, establece `TELEGRAM_ENABLED=False`
y recrea `web` y `telegram` con los mismos ficheros Compose.
