# EA1RKV - Vigo Val Miñor Radioclub Website

Wagtail CMS website for the **EA1RKV - Vigo Val Miñor Radioclub** amateur radio club.

## Primera versión: Inicio + Blog

Web de la **Unión de Radioafeccionados de Vigo-Val Miñor**, indicativo **EA1RKV**.

- Inicio con presentación editable, fotografía opcional y tres últimas publicaciones.
- Blog con artículos, imágenes, autor/indicativo, categorías, etiquetas y paginación.
- Administración Wagtail en `/admin/`: borradores, revisiones y publicación.
- Diseño adaptable a móvil y escritorio, navegación por teclado y textos públicos en español.
- Las secciones adicionales del proyecto se conservan para ampliaciones. La inicialización solo crea Inicio y Blog; el menú muestra las páginas publicadas marcadas para aparecer en él.

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

1. En **Páginas > Inicio**, modifica título, presentación y fotografía opcional. Publica los cambios.
2. En **Inicio > Blog**, usa **Añadir página > Blog Post**. Rellena título, fecha, resumen y cuerpo; añade una imagen y autor si lo deseas.
3. Guarda un borrador o pulsa **Publicar**. Las entradas públicas aparecen automáticamente en el blog y en Inicio.
4. En **Ajustes > Radioclub Settings**, introduce los datos reales de contacto y el nombre del club. Las redes se configuran en **Social Media Settings**.
5. Las páginas privadas y los borradores no aparecen en los listados públicos ni en el RSS.

### GitHub Codespaces

Abre un Codespace en la rama de esta versión. La configuración instala dependencias, aplica migraciones e inicializa Inicio y Blog. Después ejecuta `python manage.py runserver 0.0.0.0:8000` y abre el puerto 8000. La configuración existente crea `admin` / `admin` para desarrollo; cambia esa contraseña y no la uses en producción.

### Verificación

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test ea1rkv.apps.home
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

After initial setup, configure the site through the Wagtail admin at `/admin/`:

1. **Settings > Radioclub Settings** - Club callsign, address, grid locator
2. **Settings > Social Media** - Facebook, Twitter, Instagram, YouTube, QRZ links
3. **Pages > Home** - Edit hero section, about text
4. Create child pages: Blog, Events, Gallery, Members, Contact

## License

This project is for the EA1RKV Radioclub. See repository for license details.

