# Galego, español e inglés

La migración crea los tres idiomas. Wagtail ofrece la acción Traducir mediante
simple_translation, sin claves ni servicios externos.

1. Actualiza y reconstruye el servicio web con el Compose habitual. El arranque
   aplica la migración; la construcción compila los catálogos de interfaz.
2. En Páginas, abre las acciones de Inicio y elige Traducir. Selecciona Galego
   o English. Traduce los campos de la copia, revisa y publica.
3. Repite con Blog, Servicios e Indicativos especiales y luego sus páginas hijas.
   Traduce primero los padres. Conserva el nombre propio oficial del club.
4. Cada idioma tiene su propio borrador y publicación. Cambiar español no
   sobrescribe las traducciones; actualízalas cuando cambie el original.

El selector muestra los tres nombres; únicamente enlaza las traducciones públicas
y publicadas de la página actual. Un idioma sin traducción aparece desactivado.
No redirige a una página distinta ni muestra borradores. La navegación usa la raíz
traducida. Español conserva /; galego usa /gl/ e inglés /en/. /admin/ es estable.

No se crean traducciones automáticas de los textos editoriales ni se publican
copias en español bajo otro idioma. Los títulos, descripciones, artículos,
categorías y fichas requieren traducción editorial. Los textos comunes de portada,
listado del blog y biblioteca disponen de catálogos gl/en; otras plantillas
secundarias pueden conservar etiquetas españolas.

En desarrollo, instala GNU gettext y ejecuta:
```bash
django-admin compilemessages
python manage.py migrate
```

No cambies la raíz del sitio ni crees un Site distinto por idioma.
