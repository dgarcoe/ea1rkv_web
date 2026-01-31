# EA1RKV - Vigo Val Miñor Radioclub Website

Wagtail CMS website for the **EA1RKV - Vigo Val Miñor Radioclub** amateur radio club.

## Features

- **Blog** - News, articles, and technical posts with categories and tags
- **Events** - Contests, field days, meetings, and workshops calendar
- **Photo Gallery** - Image galleries with lightbox viewer
- **Members Directory** - Club members with callsigns, roles, and QRZ links
- **Contact Form** - Configurable form with email notifications
- **Search** - Full-text search across all content
- **RSS Feed** - Syndication feed for blog posts
- **Multilingual** - Spanish, Galician, and English support
- **SEO** - Built-in Wagtail SEO features and sitemaps
- **Responsive** - Bootstrap 5 mobile-first design
- **Radio-specific fields** - Grid locators, frequencies, modes, callsigns

## Tech Stack

- **Backend**: Django 5.1 + Wagtail 6.3
- **Database**: PostgreSQL 16
- **Frontend**: Bootstrap 5 + Bootstrap Icons
- **Caching**: Redis (production)
- **Server**: Gunicorn + Nginx (production)
- **Containerization**: Docker + Docker Compose

## Quick Start (GitHub Codespaces)

1. Click **"Code" > "Codespaces" > "Create codespace on main"** in the GitHub repo
2. Wait for the container to build and the post-create script to finish
3. The site will be available at the forwarded port **8000**
4. Admin panel: `/admin/` (login: `admin` / `admin`)

## Local Development

### Prerequisites

- Docker and Docker Compose

### Setup

```bash
# Clone the repository
git clone https://github.com/dgarcoe/ea1rkv_web_example.git
cd ea1rkv_web_example

# Build and start containers
make build
make up

# Run migrations and create superuser
make migrate
make createsuperuser

# Open the site
# http://localhost:8000/
# http://localhost:8000/admin/
```

### Useful Commands

```bash
make help            # Show all available commands
make up              # Start development server
make down            # Stop containers
make logs            # Tail web container logs
make shell           # Open Django shell
make migrate         # Run database migrations
make makemigrations  # Create new migrations
make test            # Run tests
make lint            # Run linter
make format          # Format code
```

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
