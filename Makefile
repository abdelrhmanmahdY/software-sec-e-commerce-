.PHONY: setup up down restart logs migrate seed reset check test shell superuser

# Docker Compose creates the local certificates, database, migrations, and demo data.
# This target needs Docker Compose, but not Bash, mkcert, Python, PostgreSQL, or Make-specific shell tools.
setup:
	docker compose up -d --build --wait

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