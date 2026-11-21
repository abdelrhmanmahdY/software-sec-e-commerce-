# Secure E-Commerce Platform — TLS and AAA

A Dockerized Django e-commerce web application developed as a Software Security project. The project combines an e-commerce workflow with security controls related to **Authentication, Authorization, and Accounting (AAA)** and HTTPS communication through an Nginx reverse proxy.

## 1. Project overview

The application is organized into Django modules for the main e-commerce and security responsibilities:

- **Users and authentication:** user accounts and login-related functionality.
- **Products:** product catalogue and product information.
- **Carts and orders:** shopping-cart and order workflows.
- **Dashboard:** application dashboard pages.
- **Audit:** records security-relevant activity for accounting and review.

### AAA security model

| AAA area | Purpose | Project location |
|---|---|---|
| Authentication | Verify the identity of a user, including login and session handling. | `users/` and authentication configuration |
| Authorization | Control which actions and resources an authenticated user is allowed to access. | Django views, permissions, and application modules such as `products/`, `orders/`, and `dashboard/` |
| Accounting | Record relevant actions and events so activity can be reviewed. | `audit/` and audit middleware |

The project also includes HTTPS configuration, secure session/CSRF cookie settings, and configurable login lockout settings. The exact protection provided by each feature depends on its implementation and tests.

## 2. Technology stack

- **Backend:** Python 3.12, Django, Gunicorn
- **Database:** PostgreSQL 16
- **Reverse proxy / HTTPS:** Nginx
- **Containers:** Docker and Docker Compose
- **Local development certificates:** mkcert (recommended for browser-trusted HTTPS on `localhost`)

## 3. Application architecture

```text
Browser
   |
   | HTTPS :443
   v
Nginx (TLS termination / reverse proxy)
   |
   | HTTP inside the Docker network
   v
Django + Gunicorn (web)
   |
   v
PostgreSQL (db)
```

Docker Compose also starts the certificate setup service used by this project. Django initialization is handled by the container entrypoint, which runs database migrations and collects static files before starting Gunicorn. Seed data and superuser creation can also be configured through the environment variables supported by the entrypoint.

## 4. Requirements

Install the following on your development machine:

- Docker Engine
- Docker Compose v2 (`docker compose`)
- GNU Make
- Git (if you are cloning the repository)
- mkcert and `libnss3-tools` for a locally trusted development certificate on Ubuntu

Check that Docker is available:

```bash
docker --version
docker compose version
make --version
```

## 5. First-time setup

### Step 1 — Open the project directory

Run these commands from the directory containing `docker-compose.yml` and the `Makefile`:

```bash
cd /path/to/project
```

### Step 2 — Create the environment file

The `make setup` target copies `.env.example` to `.env` if `.env` does not already exist. You can also do this manually:

```bash
cp -n .env.example .env
```

Open `.env` and review the configuration. Set strong, unique values for passwords and secrets. Do not commit `.env` to Git.

Common settings may include:

```env
SECRET_KEY=replace-with-a-long-random-secret
POSTGRES_DB=nexus
POSTGRES_USER=nexus
POSTGRES_PASSWORD=replace-with-a-strong-database-password
POSTGRES_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://localhost,https://127.0.0.1
LOGIN_MAX_FAILURES=5
LOGIN_LOCKOUT_MINUTES=15
```

Use the actual variable names and defaults defined in your `.env.example` and `docker-compose.yml`; do not add variables unless the application reads them.

### Step 3 — Configure local HTTPS (recommended)

For a certificate trusted by your local browser, install mkcert on Ubuntu and install its local development CA:

```bash
sudo apt update
sudo apt install -y mkcert libnss3-tools
mkcert -install
```

Generate the certificate files expected by this project's Compose configuration:

```bash
mkdir -p certs
mkcert \
  -cert-file certs/fullchain.pem \
  -key-file certs/privkey.pem \
  localhost 127.0.0.1 ::1
```

**Important:** the Compose `certs` service runs `scripts/generate_certs.sh`. Check that this script preserves existing certificate files before relying on the mkcert certificate above. If it overwrites them with a self-signed certificate, the browser may show a certificate warning. The private key `certs/privkey.pem` must remain local and must not be committed.

### Step 4 — Build and start the application

Run:

```bash
make setup
```

The current `setup` target:

1. Copies `.env.example` to `.env` only if `.env` does not already exist.
2. Builds the Docker images.
3. Starts the services in the background.

When the containers are running, open:

- **Application:** https://localhost
- **Django admin:** https://localhost/admin/ (when the admin route is enabled)

The web application is served through Nginx on the host's HTTPS port `443`.

## 6. Makefile commands

Run these commands from the project root. They are shortcuts for common Docker Compose and Django management tasks.

| Command | Purpose |
|---|---|
| `make setup` | First-time setup: create `.env` if missing, build images, and start the services. |
| `make up` | Build images if needed and start services in the background. |
| `make down` | Stop and remove the Compose containers and network. Named volumes are retained. |
| `make restart` | Stop the Compose project, then rebuild and start it again. |
| `make logs` | Follow logs from the `web`, `nginx`, and `db` services. |
| `make migrate` | Apply Django database migrations. |
| `make seed` | Run the project's `seed_data` management command. |
| `make reset` | Run `seed_data --clear`. This may remove existing seeded records; check the command implementation before using it on data you need. |
| `make check` | Run Django system checks and check whether model changes require migration files. |
| `make test` | Run the Django test suite. |
| `make shell` | Open the Django interactive shell inside the `web` container. |
| `make superuser` | Create a Django superuser interactively. |

### Typical daily workflow

After the first setup, the usual workflow is:

```bash
make up       # Start the application
make logs     # Inspect application logs when needed
make test     # Run tests
make down     # Stop the application when finished
```

To restart after changing application code or Docker build configuration:

```bash
make restart
```

To create an administrator account:

```bash
make superuser
```

If the application already created a superuser from environment variables, you do not need to create another one. To change an existing user's password, use Django's supported password-management workflow rather than creating duplicate accounts.

## 7. Equivalent Docker Compose commands

You can run the underlying commands directly without Make:

```bash
# Build and start all services
docker compose up -d --build

# List service status
docker compose ps

# Follow logs
docker compose logs -f web nginx db

# Run migrations
docker compose exec web python manage.py migrate

# Run tests
docker compose exec web python manage.py test

# Open Django shell
docker compose exec web python manage.py shell

# Stop containers (keeps named volumes)
docker compose down
```

## 8. Data and persistence

The Compose configuration uses named volumes for PostgreSQL data, uploaded media, and application data. Running `make down` or `docker compose down` does not normally delete these volumes, so database and media data are retained when containers are stopped and removed.

Avoid this command unless you intentionally want to delete the stored Compose data:

```bash
docker compose down -v
```

The `-v` option removes named volumes and can permanently delete the local database, uploaded media, and application data.

## 9. Troubleshooting

### Check whether all services are running

```bash
docker compose ps
```

### Inspect service logs

```bash
docker compose logs --tail=100 web nginx db
```

### Check whether the HTTPS endpoint responds

```bash
curl -Iv https://localhost
```

### Check the certificate served by Nginx

```bash
echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

### Check for port conflicts

The Compose configuration publishes ports `80`, `443`, and (by default) `5432` on the host. Check whether another service is using one of them:

```bash
sudo ss -ltnp | grep -E ':(80|443|5432)\b'
```

If a service cannot start, inspect its logs before changing ports or deleting volumes.

### Browser reports that the connection is not secure

A working HTTPS response does not by itself prove that the browser trusts the certificate. Confirm that:

1. Nginx is serving the mkcert certificate, not a self-signed fallback certificate.
2. mkcert's local CA has been installed in the trust store used by the browser.
3. The certificate includes `localhost` in its Subject Alternative Names.
4. The page does not load active resources over plain HTTP (mixed content).

Use the browser's Developer Tools **Security** panel and Console to identify certificate or mixed-content warnings.

## 10. Development and security notes

- This setup is intended for local development and academic demonstration. Do not expose it to the public internet without a production security review.
- Replace development passwords, database credentials, and Django secret keys with strong unique values.
- Keep `.env`, `certs/privkey.pem`, and any other private credentials out of version control.
- Local mkcert certificates are for development. Use a certificate issued and managed for your actual production domain in a deployed environment.
- Run `make check` and `make test` after security-related changes.
- A successful Django `check` is not a complete AAA security audit. Authentication, authorization, and audit logging should also have dedicated tests covering allowed and denied actions, ownership checks, failed logins, and recorded audit events.

## 11. Quick reference

```bash
# First run
make setup

# Open in browser
# https://localhost

# Normal start / stop
make up
make down

# Quality checks
make check
make test

# Django administration
make migrate
make superuser
make shell

# Logs and service status
make logs
docker compose ps
```