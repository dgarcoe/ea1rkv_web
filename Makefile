# EA1RKV Wagtail Site - Development Commands
.PHONY: help build up down logs shell migrate makemigrations createsuperuser test lint format clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Docker commands ---

build: ## Build Docker containers
	docker compose build

up: ## Start development server
	docker compose up -d

down: ## Stop all containers
	docker compose down

logs: ## Tail container logs
	docker compose logs -f web

restart: ## Restart the web container
	docker compose restart web

# --- Django commands (run inside container) ---

shell: ## Open Django shell
	docker compose exec web python manage.py shell

dbshell: ## Open database shell
	docker compose exec db psql -U ea1rkv ea1rkv

migrate: ## Run database migrations
	docker compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker compose exec web python manage.py makemigrations

createsuperuser: ## Create admin superuser
	docker compose exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	docker compose exec web python manage.py collectstatic --noinput

# --- Quality commands ---

test: ## Run tests
	docker compose exec web pytest

lint: ## Run linter (ruff)
	docker compose exec web ruff check .

format: ## Format code (ruff)
	docker compose exec web ruff format .

lint-templates: ## Lint Django templates (djlint)
	docker compose exec web djlint ea1rkv/templates/ --lint

format-templates: ## Format Django templates (djlint)
	docker compose exec web djlint ea1rkv/templates/ --reformat

# --- Production commands ---

prod-build: ## Build production containers
	docker compose -f docker-compose.prod.yml build

prod-up: ## Start production server
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production containers
	docker compose -f docker-compose.prod.yml down

prod-migrate: ## Run production migrations
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate

prod-logs: ## Tail production logs
	docker compose -f docker-compose.prod.yml logs -f

# --- Cleanup ---

clean: ## Remove all containers, volumes, and cached files
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
