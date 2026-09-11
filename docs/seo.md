# SEO de EA1RKV

La web incluye títulos y descripciones por página, URL canónica, variantes
`hreflang` para español, galego e inglés, Open Graph, datos estructurados,
`robots.txt` y un sitemap con todos los árboles traducidos publicados.

## Despliegue

Producción usa por defecto `ea1rkv.com` y el puerto 443 para las URL del
sitemap. Se puede declarar explícitamente en `.env`:

```env
WAGTAIL_SITE_HOSTNAME=ea1rkv.com
WAGTAIL_SITE_PORT=443
```

El arranque actual ejecuta `setup_radioclub`, que sincroniza estos valores con
**Ajustes > Sitios** de Wagtail sin modificar contenido editorial.

Después de desplegar, comprueba:

```bash
curl -sS https://ea1rkv.com/robots.txt
curl -sS https://ea1rkv.com/sitemap.xml
curl -sS https://ea1rkv.com/ | grep -E 'canonical|hreflang|ld\+json'
```

## Search Console

1. Añade una propiedad de dominio para `ea1rkv.com`.
2. Verifica el dominio con el registro TXT que proporciona Google.
3. Envía `https://ea1rkv.com/sitemap.xml`.
4. Solicita la indexación de la portada, Servicios e Indicativos especiales.
5. Revisa cada mes consultas, páginas, países, dispositivos y errores de
   indexación. No cambies URL publicadas sin crear una redirección permanente.

`GOOGLE_SITE_VERIFICATION` admite el token de una propiedad de prefijo de URL,
pero la propiedad de dominio mediante DNS es preferible porque cubre todas las
variantes del dominio y protocolo.

## Edición en Wagtail

En la pestaña **Promocionar** de cada página:

- Usa una etiqueta de título concreta, no «Inicio». La portada ya aplica como
  reserva «EA1RKV | Radioafición y radioclub en Vigo y Val Miñor».
- Escribe una descripción distinta que explique qué encontrará la persona.
- Mantén una sola cabecera H1 y utiliza H2/H3 para organizar el texto.
- Añade texto alternativo descriptivo a las imágenes; una imagen decorativa
  debe tener alternativa vacía.
- Traduce también título SEO y descripción en cada versión de la página.

Si una descripción SEO está vacía, se usa el resumen o introducción de la
página y, como último recurso, una descripción general localizada.

## Contenido para búsquedas locales

La posición no se puede garantizar. Para competir por búsquedas locales, el
contenido debe resolver preguntas reales y mantenerse actualizado:

- Página estable y precisa de repetidores y frecuencias de Vigo y Val Miñor.
- Artículos originales sobre cobertura, modos, actividades y operación local.
- Una página completa por indicativo especial, con fechas, fotografías y
  resultados, enlazada desde otras entidades participantes cuando proceda.
- Datos reales de contacto, ubicación, redes y QRZ en **Ajustes > Radioclub**.
- Correcciones rápidas de enlaces rotos y páginas 404 detectadas por Search
  Console y GoAccess.

Evita repetir palabras clave artificialmente, copiar contenido o crear páginas
casi idénticas para cada búsqueda. La utilidad, precisión y reputación externa
son señales que el código por sí solo no puede proporcionar.

## Dominio canónico

El proxy público debe redirigir de forma permanente HTTP a HTTPS y cualquier
variante `www` a `https://ea1rkv.com`. Sólo la variante canónica debe aparecer
en enlaces internos, sitemap y `hreflang`.

Referencias oficiales:

- https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/search/docs/specialty/international/localized-versions
