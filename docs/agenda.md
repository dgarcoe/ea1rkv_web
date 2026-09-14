# Agenda

Incluye calendario mensual (lunes a domingo) con navegación por meses.
En móviles se puede desplazar horizontalmente. Los indicativos especiales
publicados, públicos y del mismo idioma aparecen automáticamente si tienen
fecha de inicio, durante todos los días hasta su fecha final. Sin fecha final
se muestran sólo el día de inicio. Cada entrada enlaza con la ficha original;
no hay que duplicarla como actividad. Los filtros afectan al calendario y al
listado; el archivo afecta sólo al listado.

El arranque de producción ejecuta las migraciones y `setup_radioclub`.
Este comando crea Agenda bajo Inicio y sus versiones en galego e inglés si
existen las portadas traducidas, sin sustituir contenido editorial.

En Wagtail: Páginas → Inicio → Agenda → Añadir página → Actividad.
Completa título, tipo, fechas, horario local de Vigo, lugar, resumen,
fotografía y descripción con el editor de texto rico. Los datos de radio
son opcionales. Publica para mostrar la actividad. Usa Traducir para crear
las versiones del evento; no se traducen automáticamente.

Las actividades se ordenan por fecha y las de varios días se mantienen en
próximas hasta finalizar su último día. Después pasan al archivo. Se puede
filtrar por tipo. Una actividad sin fecha final dura un solo día.

Para cambiar la posición del menú, reordena las páginas hijas de Inicio.
No se crean actividades de ejemplo. No requiere cambios en nginx.

Despliegue habitual:

```bash
git pull --ff-only
docker compose -f docker-compose.prod.external.yml up -d --build
```

Si usas el overlay de estadísticas, conserva también
`-f docker-compose.analytics.yml` en el comando de Compose.
