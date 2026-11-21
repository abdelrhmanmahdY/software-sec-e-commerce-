# SecureShop Endpoint Map (read-only inspection)

Built by reading the current repo as a **read-only reference**. The Blue Team is still developing, so this map **will change** — update the paths when the final version lands. Nothing here was tested.

Base (local only): `http://localhost:8000`

## Auth

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| POST | `/api/auth/login/` | SimpleJWT `TokenObtainPairView` | public | returns JWT access/refresh |
| POST | `/api/auth/refresh/` | `TokenRefreshView` | public | — |
| GET/POST | `/dashboard/login/` | `dashboard.login_view` | public | session login |
| GET | `/dashboard/logout/` | `logout_view` | session | — |

## Registration / confirmation

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| GET/POST | `/dashboard/signup/` | `signup_view` | public | sets `is_active=False`, shows confirm link to user (H12) |
| GET/POST | `/signup/` | `users.RegisterView` | public, `csrf_exempt` | **may activate immediately** (H11) |
| POST | `/api/users/signup/` | `RegisterAPIView` | public | `is_active=False` |
| GET | `/dashboard/confirm/<token>/` | `confirm_email` | public | signed token, 3-day max_age (H12) |

## Catalogue

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| GET | `/dashboard/shop/` | `shop_view` | session | search, category, max_price, sort |
| POST | `/dashboard/shop/` | `shop_view` | session | add to cart |
| GET | `/dashboard/products/<pk>/` | `product_detail` | session | — |
| GET | `/api/products/products/` | `ProductViewSet` | read: public | filter/search/order |
| POST/PUT/PATCH/DELETE | `/api/products/products/` | `ProductViewSet` | staff only | `IsAdminOrReadOnly` |
| POST | `/api/products/ajax/add-category/` | `ajax_add_category` | `login_required`, `csrf_exempt` | **no staff check** (H15) |

## Cart

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| GET | `/api/carts/cart/` | `CartDetailView` | JWT | — |
| POST | `/api/carts/cart/add/` | `AddToCartView` | JWT | `quantity` via `int()` (H7) |
| DELETE | `/api/carts/cart/remove/<product_id>/` | `RemoveFromCartView` | JWT | — |
| POST | `/api/carts/cart/update-quantity/` | `UpdateCartItemQuantityView` | **no `login_required`** (H9) | returns `str(e)` (H8) |
| POST | `/api/carts/orders/checkout/` | `carts.CheckoutView` | `login_required` | coupon + store credit (H1, H3) |

> ⚠️ Frontend mismatch (H10): `cart.html` calls `/api/cart/update-quantity/` but the route is `/api/carts/cart/update-quantity/`. Also the name `checkout` is registered in both `carts/urls.py` and `orders/urls.py`.

## Orders

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| GET/POST/PUT/PATCH/DELETE | `/api/orders/orders/` | `OrderViewSet` | `IsAuthenticated` | `queryset = all()`, **no per-user filter** (H5) |
| GET/POST/... | `/api/orders/order-items/` | `OrderItemViewSet` | `IsAuthenticated` | `price` writable (H6) |
| POST | `/api/orders/checkout/` | `orders.CheckoutView` | JWT | **no payment/stock/coupon** (H2) |
| GET | `/dashboard/orders/` | `orders_list` | session | non-staff see own; staff see all |
| POST | `/dashboard/orders/create/` | `order_create` | session | status chooseable (H17) |
| POST | `/dashboard/orders/<pk>/update/` | `order_update` | staff | — |
| POST | `/dashboard/orders/<pk>/delete/` | `order_delete` | staff | — |

## Coupons / newsletter

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| POST | `/dashboard/newsletter/signup/` | `newsletter_signup` | public | code = `NEWS` + user count (H4) |
| (checkout) | `coupon_code` in `/api/carts/orders/checkout/` | `carts.CheckoutView` | — | reusable? (H3) |

## Profile / account

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| GET | `/dashboard/profile/` | `profile` | session | — |
| GET/POST | `/dashboard/settings/` | `settings` | session | update profile |
| POST | `/dashboard/password/change/` | `password_change` | session | — |
| POST | `/dashboard/user/<pk>/delete/` | `user_delete` | session | checks own id |
| GET | `/api/users/me/` | `UserProfileView` | JWT | — |

## Admin

| Method | Path | View | Auth | Notes |
|---|---|---|---|---|
| GET | `/dashboard/` , `/dashboard/admin-dashboard/` | `admin_dashboard` | staff | — |
| GET | `/dashboard/users/` | `users_list` | staff | — |
| POST | `/dashboard/users/<pk>/role/` | `user_update_role` | staff | staff can promote/demote (H16) |
| POST | `/dashboard/users/<pk>/delete/` | `admin_user_delete` | staff | — |
| * | `/admin/` | Django admin | superuser | — |
| GET | `/api/docs/`, `/api/redoc/` | drf-yasg | public | schema public (H22) |

## Auth model summary

- **Two auth systems in parallel:** SimpleJWT for `/api/...` and Django session for `/dashboard/...`.
- **Authorization:** `@user_passes_test(lambda u: u.is_staff)` for admin pages; `IsAdminOrReadOnly` for products; `IsAuthenticated` (no object-level check) for orders.
- **Password storage:** Django default (PBKDF2) — no custom `PASSWORD_HASHERS` (H20).
- **No rate limiting / lockout / throttling** configured (H13).

## Money / price / coupon handling (where to focus)
- Price source: `Product.price` (DB) in `carts/views.py` checkout — good; but Orders API serializer lets `price` be written (H6).
- Coupon: `carts/views.py` lines ~100–109; no used-coupon tracking (H3).
- Store credit: `UserProfile.store_credit`; checkout deducts `min(credit, total)` but still creates the order if credit < total (H1).
