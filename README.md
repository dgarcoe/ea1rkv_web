# EA1RKV - Vigo Val Miñor Radioclub Website

Wagtail CMS website for the **EA1RKV - Vigo Val Miñor Radioclub** amateur radio club.

## Inicio, Blog, Servicios e Indicativos especiales

Web de la **Unión de Radioafeccionados de Vigo-Val Miñor**, indicativo **EA1RKV**.

## Actualizar una instalación existente

Después de descargar los cambios, ejecuta estos comandos en el mismo entorno donde arrancas la web:

```bash
python manage.py migrate
python manage.py setup_radioclub
```

Reinicia el servidor. Es necesario aplicar las migraciones antes de abrir `/admin/`; no borres la base de datos. El segundo comando añade las nuevas secciones al menú y a la portada sin duplicarlas ni sobrescribir sus textos.

### Servicios

En **Páginas > Inicio > Servicios**, edita la presentación o añade una página **Servicio / recurso**. Elige Repetidores, Frecuencias, Equipos de radio u Otros servicios. Completa el resumen, descripción en texto enriquecido y los datos que correspondan: frecuencia/salida y entrada en MHz, modo, tono o parámetros de acceso, ubicación/cobertura, modelo, disponibilidad y fotografía. Las fichas se agrupan por tipo y conservan el orden del árbol de páginas. Guarda borradores o publica cuando los datos estén confirmados.

### Indicativos especiales

En **Páginas > Inicio > Indicativos especiales**, añade una página **Indicativo especial** por actividad. Incluye título, indicativo, resumen, fechas opcionales, portada o diploma, enlace a QRZ e información/QSL en texto enriquecido.

En **Álbum de fotos** selecciona imágenes y añade pies, créditos y, si lo deseas, un nombre de grupo. Puedes ordenar las fotos; las que comparten grupo se muestran juntas. Cada foto se puede ampliar y descargar. La descripción se escribe en un solo editor, sin bloques. También puedes insertar enlaces a documentos y vídeos mediante el editor.

La organización por indicativo, fechas, descripción, QRZ y grupos de fotografías toma como referencia la rama `claude/fix-youtube-description-style-lYxVS` de `special_callsign_media_sharing_web`. Esta versión administra el contenido en Wagtail; no importa datos ni conecta con la base de Quendaward. Las imágenes se sirven con el almacenamiento habitual de Wagtail; restringir una página no convierte sus archivos multimedia en archivos privados.

Las secciones comienzan vacías: no se añaden frecuencias, equipos ni indicativos de ejemplo como si fueran recursos reales del club.

- Inicio con presentación editable, fotografía opcional y tres últimas publicaciones.
- Blog con artículos, imágenes, autor/indicativo, categorías, etiquetas y paginación.
- Administración Wagtail en `/admin/`: borradores, revisiones y publicación.
- Diseño adaptable a móvil y escritorio, navegación por teclado y textos públicos en español.
- Servicios e Indicativos especiales con fichas editables y álbumes de fotografías. La inicialización crea las cuatro secciones; el menú muestra las páginas publicadas marcadas para aparecer en él.

## Puesta en marcha local (Python 3.12)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt
python manage.py migrate
python manage.py setup_radioclub
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://localhost:8000/` y `/admin/`. El sitio usa el idioma español bajo `/es/` (la raíz redirige) y SQLite en desarrollo. No necesitas Docker para empezar.

`setup_radioclub` crea la portada y el blog en una base nueva. Se puede repetir sin duplicar páginas ni sobrescribir textos. Si encuentra otra portada personalizada, se detiene con instrucciones; no elimina páginas. No crea noticias ficticias ni inventa datos de contacto.

### Editar y publicar

1. En **Páginas > Inicio**, modifica el título y, en **Cabecera > Imagen de cabecera**, sube o selecciona tu foto de Vigo. Se muestra a todo lo ancho detrás del indicativo, con una capa oscura para facilitar la lectura. Puedes sustituirla o quitarla en cualquier momento. Usa **Créditos de la imagen** para el autor, fuente y licencia. Publica los cambios.
2. En **Inicio > Blog**, usa **Añadir página > Blog Post**. Rellena título, fecha, resumen y **Contenido**; añade una imagen y autor si lo deseas.
3. Guarda un borrador o pulsa **Publicar**. Las entradas públicas aparecen automáticamente en el blog y en Inicio.
4. En **Ajustes > Radioclub Settings**, introduce los datos reales de contacto y el nombre del club. Las redes se configuran en **Social Media Settings**.
5. Las páginas privadas y los borradores no aparecen en los listados públicos ni en el RSS.

### Editor de texto enriquecido

La portada incluye una descripción inicial del radioclub, su vocación de aprendizaje y lo que se encontrará en la web. Puedes reescribirla por completo en **Páginas > Inicio > Presentación del radioclub > Contenido** y pulsar **Publicar**. Al actualizar, solo se sustituye el texto inicial anterior; se respetan las modificaciones editoriales.

Inicio y los artículos tienen un único campo **Contenido**, con barra de formato para títulos, negrita, cursiva, listas, enlaces, imágenes y contenido incrustado. No es necesario añadir bloques o secciones. En Inicio puedes escribir la presentación completa en ese campo.

Para actualizar una instalación existente ejecuta `python manage.py migrate`. La migración convierte la presentación y los bloques anteriores a texto enriquecido, incluidos los borradores y revisiones. Las tarjetas se convierten en contenido consecutivo, y las citas en párrafos; los datos originales se conservan ocultos para recuperación. Esta migración de contenido no admite reversión automática; haz una copia de la base antes de actualizar. La foto la elige y sube el club.

### GitHub Codespaces

Abre un Codespace en la rama de esta versión. La configuración instala dependencias, aplica migraciones e inicializa las cuatro secciones. Después ejecuta `python manage.py runserver 0.0.0.0:8000` y abre el puerto 8000. La configuración existente crea `admin` / `admin` para desarrollo; cambia esa contraseña y no la uses en producción.

### Verificación

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test ea1rkv.apps.home ea1rkv.apps.club
```

Se comprueban la inicialización repetible, portada/blog vacíos, publicación y privacidad, paginación, imágenes y acceso al panel.

Esta rama incluye las migraciones iniciales que faltaban en el repositorio. Si ya creaste tablas manualmente en otra instalación, revisa su correspondencia antes de aplicar migraciones; las instrucciones anteriores están verificadas sobre una base vacía.

## Entorno

Se mantiene la configuración Django/Wagtail del repositorio, con PostgreSQL y Docker disponibles para producción. Bootstrap se carga desde CDN. Antes de publicar en Internet, configura dominio, HTTPS, credenciales y copias de seguridad y revisa las versiones soportadas de Django/Wagtail.

## Production Deployment (VPS with Docker)

### 1. Prepare the server

```bash
# Copy files to your VPS
scp -r . user@your-vps:/opt/ea1rkv/

# SSH into the server
ssh user@your-vps
cd /opt/ea1rkv
```

### 2. Configure environment

```bash
# Create .env from the example
cp .env.example .env

# Edit .env with your production values
# IMPORTANT: Set a strong DJANGO_SECRET_KEY and POSTGRES_PASSWORD
nano .env
```

### 3. Build and launch

```bash
# Build production containers
make prod-build

# Start the stack
make prod-up

# Run migrations
make prod-migrate

# Create admin user
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 4. SSL/TLS (recommended)

For HTTPS, use a reverse proxy like Caddy or Traefik in front of Nginx, or configure Let's Encrypt with certbot.

## Project Structure

```
ea1rkv_web_example/
├── .devcontainer/          # GitHub Codespaces configuration
├── .github/workflows/      # CI/CD pipeline
├── docker/                 # Docker build files
│   ├── Dockerfile          # Development image
│   ├── Dockerfile.prod     # Production multi-stage image
│   └── nginx/              # Nginx configuration
├── ea1rkv/                 # Django project
│   ├── apps/               # Wagtail applications
│   │   ├── base/           # Shared blocks, settings, template tags
│   │   ├── blog/           # News and articles
│   │   ├── contact/        # Contact form
│   │   ├── events/         # Events calendar
│   │   ├── gallery/        # Photo galleries
│   │   ├── home/           # Homepage
│   │   ├── members/        # Members directory
│   │   └── search/         # Site search
│   ├── settings/           # Django settings (base, dev, production)
│   ├── static/             # CSS, JS, images
│   ├── templates/          # Django/Wagtail templates
│   └── urls.py             # URL configuration
├── requirements/           # Python dependencies (base, dev, production)
├── docker-compose.yml      # Development compose
├── docker-compose.prod.yml # Production compose
├── Makefile                # Development shortcuts
└── pyproject.toml          # Python tooling configuration
```

## Content Management

Consulta la [guía del editor clásico y las plantillas de indicativos](docs/editor-e-indicativos.md)
para actualizar una instalación existente y editar las nuevas fichas.

After initial setup, configure the site through the Wagtail admin at `/admin/`:

1. **Settings > Radioclub Settings** - Club callsign, address, grid locator
2. **Settings > Social Media** - Facebook, Twitter, Instagram, YouTube, QRZ links
3. **Pages > Home** - Edit hero section, about text
4. Create child pages: Blog, Events, Gallery, Members, Contact

## License

This project is for the EA1RKV Radioclub. See repository for license details.
