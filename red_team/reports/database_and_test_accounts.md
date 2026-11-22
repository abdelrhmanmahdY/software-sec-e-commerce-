# SecureShop — Database & Test Accounts (Red Team discovery)

**Phase A. Date: 2026-11-22.** Connected to the **real running database** via `docker compose exec web python manage.py shell` (Django ORM). No password hashes or secrets are printed. Target is local only.

## Database
- **Engine:** PostgreSQL 16 (Docker service `db`). Confirmed live (`connection.vendor = postgresql`).
- **Host port (Red Team run):** `127.0.0.1:5433` (remapped from 5432, which was already in use on the host). Internal app still uses `db:5432`.

## Tables (by app)
`auth_user`, `users_userprofile`, `users_coupon`, `users_couponusage`, `users_newslettersubscriber`, `products_category`, `products_product`, `carts_cart`, `carts_cartitem`, `orders_order`, `orders_orderitem`, `audit_auditlog`, `token_blacklist_*`, Django built-ins.

## Accounts (verified from DB — no secrets shown)
| id | username | staff | superuser | active | store_credit | totp | Role |
|---|---|---|---|---|---|---|---|
| 1 | `admin` | ✓ | ✓ | ✓ | 500.00 | off | **Administrator** (existing) |
| 2 | `staff` | ✓ | ✗ | ✓ | 0.00 | off | **Staff** (existing) |
| 3 | `customer` | ✗ | ✗ | ✓ | 500.00 | off | **Customer** (existing) |
| 4 | `admin@example.test` | ✗ | ✗ | ✓ | 0.00 | off | Customer (test account, pre-existing in DB) |
| 5 | `dsad@example.test` | ✗ | ✗ | ✓ | 0.00 | off | Customer (test account, pre-existing in DB) |

- **Existing seed accounts** (from `seed_data`): `admin`, `staff`, `customer`. Passwords are documented in the project README/seed (not repeated here).
- **Pre-existing test accounts:** ids 4–5 were already in the DB (created earlier through signup). Not created by this assessment.
- **Accounts created by this assessment:** none yet. Any needed will be clearly named `rt_*` and documented here.

## Data snapshot
- **Orders:** 2 — order 1 → `customer`, order 3 → `admin@example.test`. (Owner-scoped by the API.)
- **Products:** 4. **Coupons:** 5. **CouponUsage:** 0 (redemption tracking active). **Newsletter subscribers:** 6.

## Notes for testing
- Two different customer accounts exist (`customer`, `admin@example.test`), enabling a proper cross-user IDOR re-test (H5) without creating data.
- TOTP is **off** for all accounts (`totp_enabled=False`) — MFA groundwork exists in code but is not enforced on these accounts; verify whether it is required anywhere.
- `staff` has 0 store credit; `customer` and `admin` have 500 — relevant for checkout tests.
