# Evidence — H5 Broken Access Control (IDOR) on Orders API

**Date:** 2026-11-21. **Target:** `http://127.0.0.1:8000` (local Docker baseline). **Status:** CONFIRMED VULNERABILITY.

## What was done (safe, reversible)
1. Seeded data (one order id=1 owned by `customer`, user id 3).
2. Created a probe order id=2 owned by `admin` (user id 1) via the Django shell.
3. Logged in as `customer` (JWT) and listed `/api/orders/orders/`.
4. Deleted the probe order afterwards to restore the seeded state.

## Observed (real response, customer's token)
```
GET /api/orders/orders/   Authorization: Bearer <customer JWT>
HTTP 200
{"count":2,...,"results":[
  {"id":2,"user":1,"status":"Pending","items":[],"total_price":0.0},   <-- admin's order, visible to customer
  {"id":1,"user":3,"status":"Processing",...}
]}
```
Also confirmed from the other side: `staff` (user id 2) sees order id=1 (user 3) via the same endpoint.

## Why it's a vulnerability
`OrderViewSet` uses `queryset = Order.objects.all()` with only `IsAuthenticated` and no `get_queryset` owner filter or object-level permission. Any authenticated user reads (and can modify/delete) **all** orders.

## Root cause / code location
`orders/views.py:9-17` — `OrderViewSet` / `OrderItemViewSet`.

## Recommended fix (Blue Team)
Override `get_queryset` to return `Order.objects.filter(user=self.request.user)` for non-staff, and add object-level permission checks on retrieve/update/destroy.
