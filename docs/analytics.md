# GoAccess: informe privado de visitas

Integración opcional para docker-compose.prod.external.yml. No abre puertos,
no publica el informe y no modifica el Compose de Quendaward.

## Activar

Con ea1rkv_web ya en marcha, desde la raíz del repositorio:

```bash
docker compose -f docker-compose.prod.external.yml -f docker-compose.analytics.yml config --quiet
docker compose -f docker-compose.prod.external.yml -f docker-compose.analytics.yml build goaccess
docker compose -f docker-compose.prod.external.yml -f docker-compose.analytics.yml run --rm --no-deps nginx nginx -t
docker compose -f docker-compose.prod.external.yml -f docker-compose.analytics.yml up -d --no-deps nginx
```

Si falla cualquiera de las comprobaciones, detente antes del siguiente paso.
nginx -t necesita resolver ea1rkv_web en la red Docker.
Recrear nginx causa una interrupción breve; no requiere reconstruir Django.

El proxy público debe sobrescribir X-Real-IP:
```nginx
proxy_set_header X-Real-IP $remote_addr;
```
La configuración facilitada ya lo hacía. Mantén el Nginx interno sin puertos
públicos. Si tienes un CDN delante, configura la IP real en el proxy público
antes de interpretar visitantes; de otro modo estarás contando IP del CDN.
Otros contenedores en la red compartida también pueden enviar esta cabecera.

## Obtener el informe

Visita primero una página pública. En el VPS:
```bash
umask 077
bash scripts/visits-report.sh > visitas.html
```

Comprueba que termine sin errores y el archivo no esté vacío. Descárgalo por
SFTP/scp y ábrelo en el navegador. No lo publiques en static/media ni lo
subas a Git. Repite el comando para actualizarlo: no es un panel en tiempo real.
GoAccess puede descartar líneas de arranque/error como inválidas; si no hay
peticiones válidas aún, genera tráfico y vuelve a probar.

## Alcance y conservación

- Páginas, referencias, navegadores, tráfico y errores HTTP.
- Excluye admin, documentos, static, media y health del registro de análisis.
  No incluye las apps de Quendaward servidas directamente por el proxy público.
- Filtra bots conocidos; las visitas únicas son estimaciones, no personas.
- Oculta parte de la IP en el informe. Los logs originales conservan IP y
  agente de usuario: mantenlos privados y revisa la política de privacidad.
- Omite parámetros de consulta y rutas de referencia en el registro de acceso.
  Los registros de errores son independientes.
- Docker conserva hasta cinco archivos de 10 MB. No garantiza días de historial.
  El informe cubre solo los registros disponibles desde la activación.
- Recrear/eliminar el contenedor pierde sus logs. Exporta antes de redeplegar.
  El histórico permanente necesitaría almacenamiento y rotación adicionales.
- Las solicitudes de socios a páginas públicas pueden contar como visitas.

Verifica en el informe que no todos los visitantes sean la IP privada del
proxy; si ocurre, revisa X-Real-IP.

## Desactivar

```bash
docker compose -f docker-compose.prod.external.yml up -d --no-deps --force-recreate nginx
```

No uses down -v: no es necesario borrar volúmenes.

## Validación

Revisado estáticamente. Docker no se ha podido ejecutar en el entorno de edición:
las comprobaciones anteriores deben hacerse en el VPS antes de activarlo.
Este cambio no activa Search Console ni modifica el sitemap.

Referencias: https://goaccess.io/man y
https://docs.docker.com/engine/logging/drivers/json-file/
