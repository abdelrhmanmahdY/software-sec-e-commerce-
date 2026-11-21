SHELL := /bin/bash

.PHONY: setup tls-setup up down restart logs migrate seed reset check test shell superuser

# First run: configure local TLS, create .env, and start everything
setup: tls-setup
	cp -n .env.example .env
	docker compose up -d --build --wait

# Install/trust mkcert CA and generate local certificates if needed
tls-setup:
	./scripts/setup-local-tls.sh

# Normal startup
up:
	docker compose up -d --build --wait

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d --build --wait

logs:
	docker compose logs -f web nginx db

migrate:
	docker compose exec -T web python manage.py migrate

seed:
	docker compose exec -T web python manage.py seed_data

reset:
	docker compose exec -T web python manage.py seed_data --clear

check:
	docker compose exec -T web python manage.py check
	docker compose exec -T web python manage.py makemigrations --check --dry-run

test:
	docker compose exec -T web python manage.py test

shell:
	docker compose exec web python manage.py shell

superuser:
	docker compose exec web python manage.py createsuperuser