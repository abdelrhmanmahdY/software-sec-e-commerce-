#!/bin/sh
# Container start-up: secret key, migrations, static files, optional seed, then gunicorn.
set -e

# Generate a persistent SECRET_KEY on first start if none was provided.
if [ -z "$SECRET_KEY" ] || [ "${SECRET_KEY#change-this}" != "$SECRET_KEY" ]; then
  if [ ! -s /data/secret_key ]; then
    python -c "import secrets; print(secrets.token_urlsafe(64))" > /data/secret_key
    chmod 600 /data/secret_key
    echo "Generated a new SECRET_KEY in /data/secret_key"
  fi
  SECRET_KEY="$(cat /data/secret_key)"
  export SECRET_KEY
fi

# Generate a persistent PASSWORD_PEPPER on first start if none was provided.
if [ -z "$PASSWORD_PEPPER" ]; then
  if [ ! -s /data/password_pepper ]; then
    python -c "import secrets; print(secrets.token_urlsafe(64))" > /data/password_pepper
    chmod 600 /data/password_pepper
    echo "Generated a persistent PASSWORD_PEPPER in /data/password_pepper"
  fi
  PASSWORD_PEPPER="$(cat /data/password_pepper)"
  export PASSWORD_PEPPER
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${SEED_DATA:-False}" = "True" ] && [ ! -f /data/.seeded ]; then
  python manage.py seed_data && touch /data/.seeded
fi

# Optional first admin (only if it does not exist yet)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput \
    --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" 2>/dev/null || true
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -
