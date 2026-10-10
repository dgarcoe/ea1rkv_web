# Copias de seguridad

Los superusuarios disponen de **Copias de seguridad** en el menú de Wagtail.
Una copia `.ea1rkv` contiene el volcado completo de PostgreSQL, `/app/media` y
`/app/privatefiles`. No contiene `.env`, contraseñas ni certificados TLS.

## Crear y descargar

1. Entra en `/admin/` con una cuenta de superusuario.
2. Abre **Copias de seguridad** y pulsa **Crear copia completa**.
3. Descarga el archivo de la tabla y guárdalo fuera del VPS.

Las copias también quedan en el volumen Docker `backup_volume`. Contienen datos
personales y documentación privada, por lo que deben almacenarse cifradas y con
acceso restringido.

## Restaurar en un despliegue nuevo

1. Despliega la misma versión del repositorio y configura un `.env` válido.
2. Arranca los contenedores normalmente para crear los volúmenes.
3. Entra en `/admin/` como superusuario y abre **Copias de seguridad**.
4. Selecciona el `.ea1rkv`, escribe `RESTAURAR` y confirma.
5. La aplicación verifica el formato y el checksum, crea una copia preventiva
   del estado actual y después reemplaza la base de datos y los archivos.
6. Reinicia el servicio web para cerrar cualquier conexión o caché anterior:

   ```bash
   docker compose -f docker-compose.prod.external.yml restart web
   ```

No cierres el navegador ni reinicies los contenedores durante la restauración.
Para copias grandes conviene realizar la operación en una ventana de
mantenimiento. La copia preventiva queda disponible en la misma pantalla.

El proxy Nginx público que recibe `ea1rkv.com` también debe permitir el tamaño
del archivo. En su bloque `http` o `server` configura, como mínimo:

```nginx
client_max_body_size 4G;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

Después valida y recarga ese Nginx. El Nginx incluido en este repositorio ya
admite hasta 4 GB. El límite de Django puede cambiarse con la variable
`BACKUP_MAX_UPLOAD_SIZE` expresada en bytes.

## Qué queda fuera

El archivo no incluye `.env`, certificados de Let's Encrypt, configuración del
proxy público ni el propio código Git. Para una recuperación completa conserva
por separado:

- una copia segura del `.env`;
- la URL y el commit/tag del repositorio desplegado;
- la configuración y certificados del proxy HTTPS.
