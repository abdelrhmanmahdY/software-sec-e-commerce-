FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements.txt

COPY . .

# Run as an unprivileged user
RUN useradd --create-home --uid 1000 app && mkdir -p /app/media /app/staticfiles /data && chown -R app:app /app /data
USER app

EXPOSE 8000

# Gunicorn speaks plain HTTP on the private Docker network; nginx terminates TLS.
CMD ["/app/docker-entrypoint.sh"]
