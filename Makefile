SHELL := /bin/bash

.PHONY: setup up down restart migrate seed reset check test logs shell superuser

setup:
	cp -n .env.example .env
	docker compose up -d --build
	docker compose exec -T web python manage.py migrate
	docker compose exec -T web python manage.py seed_data

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d --build

migrate:
	docker compose exec -T web python manage.py migrate

seed:
	docker compose exec -T web python manage.py seed_data

reset:
	docker compose exec -T web python manage.py seed_data --clear

check:
	docker compose exec -T web python manage.py check
	docker compose exec -T web python manage.py makemigrations --check --dry-run
	docker compose exec -T web python manage.py test

logs:
	docker compose logs -f web db

shell:
	docker compose exec web python manage.py shell

superuser:
	docker compose exec web python manage.py createsuperuser
