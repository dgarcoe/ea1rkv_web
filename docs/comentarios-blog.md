# Comentarios del blog

Tras actualizar y reconstruir el despliegue, el arranque aplica la migración.
Edita una entrada, marca **Permitir comentarios** y publica los cambios.
Las entradas existentes empiezan con los comentarios cerrados.

En **Comentarios del blog**, filtra por **Pendiente**, abre un comentario,
cambia su estado a **Aprobado** o **Rechazado** y guarda. Solo los aprobados
aparecen públicamente. Cerrar comentarios impide nuevos envíos pero conserva
los ya aprobados. Puedes eliminarlos desde la administración.

Los superusuarios tienen acceso; para delegar moderación concede al grupo
los permisos de ver, cambiar y, si procede, eliminar comentarios.

Se pide nombre o indicativo, texto y aceptación de publicación. No se solicita
correo. Hay CSRF, campo trampa, límite de 3.000 caracteres y un envío por minuto
por dirección de origen (solo hash temporal en caché). Detrás del proxy, si
Django recibe una IP compartida, ese límite también se comparte. No se usa una
cabecera IP suministrada por el cliente sin verificación.

Cada versión de idioma de una entrada conserva sus propios comentarios.
Las respuestas son texto plano escapado. No hay notificaciones por correo;
revisa los pendientes desde Wagtail.
