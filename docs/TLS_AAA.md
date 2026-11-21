# TLS (HTTPS) and AAA

## 1. TLS / HTTPS

```
Browser --TLS 1.2/1.3--> nginx :443 --plain HTTP (private docker network)--> gunicorn :8000 --> Django
```

* `nginx/default.conf` terminates TLS (TLS 1.2+1.3 only, AEAD/forward-secret ciphers), redirects :80 -> :443,
  and **overwrites** `X-Forwarded-For` so clients cannot forge their IP in the audit log.
* `web` is only `expose`d to nginx; it is not reachable from the host network. Django also redirects any
  plain-HTTP request (`SECURE_SSL_REDIRECT`) and marks session/CSRF cookies `Secure`.
* HSTS is controlled by `SECURE_HSTS_SECONDS` (default 0).

### Local / dev (self-signed)
```bash
docker compose up --build   # certs, SECRET_KEY, migrations, demo data: all automatic
# open https://localhost  (browser warns: self-signed)
```

### Production
* **Railway / Heroku / Render**: the platform already terminates TLS. Keep `USE_HTTPS=True` (default when
  `DEBUG=False`), set `SECRET_KEY`, `ALLOWED_HOSTS`, and later `SECURE_HSTS_SECONDS=31536000`.
* **Own server (docker compose)**: use a CA certificate instead of the self-signed one, e.g. Let's Encrypt:
  ```bash
  sudo certbot certonly --standalone -d shop.example.com
  cp /etc/letsencrypt/live/shop.example.com/fullchain.pem certs/fullchain.pem
  cp /etc/letsencrypt/live/shop.example.com/privkey.pem   certs/privkey.pem
  ```
  Then set `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` in `.env`, uncomment OCSP stapling in
  `nginx/default.conf`, and renew with `certbot renew` + `docker compose restart nginx`.
* Roll HSTS out gradually (300 -> 86400 -> 31536000); browsers cache it.

Verify: `curl -I http://host` (301), `openssl s_client -connect host:443 -tls1_1` (must fail),
and test the domain at https://www.ssllabs.com/ssltest/.

## 2. AAA

### Authentication
| Control | Where |
|---|---|
| Lockout: 5 failures / 15 min per username+IP, 20 per IP (spraying); applies to dashboard, `/admin/` and JWT | `audit/backends.py`, `audit/utils.py`, `settings.py` |
| JWT: 15-min access, 1-day refresh, rotation + blacklist, `POST /api/auth/logout/` revokes a token | `settings.SIMPLE_JWT`, `audit/views.py` |
| Password min length 10 + Django validators | `settings.py` |
| 30-min sliding session timeout, HttpOnly/Secure/SameSite cookies | `settings.py` |
| Account confirmation link is **e-mailed**, no longer shown on the page (only when `DEBUG`) | `dashboard/views.py` |
| DRF throttling (60/min anon, 300/min user) | `settings.py` |

### Authorization
* `users/permissions.py`: `staff_required` (real 403) and DRF `IsStaff`, `IsStaffOrCreateReadOnly`.
* **Fixed**: any logged-in user could list/edit every order via `/api/orders/` (IDOR) - now owner-only, edits staff-only.
  Client-supplied prices/status on order creation are ignored (price comes from the product).
  `/api/orders/order-items/` is staff-only. Category creation endpoint was login-only + CSRF-exempt: now staff-only + CSRF.
  Product delete was a GET link: now POST-only. Cart quantity endpoint requires login and rejects quantity < 1.
  Admins cannot change their own role.

### Accounting
* `audit.AuditLog` records: login success/failure/lockout, logout, 403s, and create/update/delete of
  User, UserProfile (store credit), Product, Category, Order, Coupon - with actor, IP, user-agent, path and
  old -> new values. Passwords are recorded only as `changed`.
* View it at **Dashboard -> Audit** (staff) or in `/admin/` (read-only; no add/change/delete). Events also go
  to stdout (`docker compose logs web`).
* For real tamper-resistance, ship the stdout stream to an external log store (the DB table alone can be edited by a DB admin).

## Notes / not covered
* `TRUST_PROXY_HEADERS` must stay on only behind a proxy that overwrites `X-Forwarded-For` (nginx here).
* DRF throttle counters are per-process (local-memory cache); use Redis for exact limits across workers.
* Database connection TLS (`?sslmode=require` in `DATABASE_URL`) is a separate setting for hosted Postgres.
