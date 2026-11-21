# Lab 1 — Excessive Trust in Client-Side Controls

**Course reference:** Lab 1, slides 19–26. Business-logic vulnerability #1.
**Type:** Practical Attack.
**Status:** Walkthrough ready (DEMO). Real PortSwigger evidence needs a manual step from you.

---

## 1. The vulnerability (plain)

The shop sends the item's **price** to the server as a normal, editable request parameter, and the server **trusts it** instead of recomputing the real price itself. Anything the client can see, the client can change — so trusting a price that came from the browser means the attacker sets their own price.

## 2. Objective

Buy the "Lightweight l33t leather jacket" ($1,337) even though store credit is only $100.

## 3. Attack, step by step (PortSwigger lab)

Credentials: `wiener : peter`.

1. With Burp proxying, log in and open the jacket page, click **Buy now**. The order is rejected (credit $100 < price $1,337). This confirms the price check exists — the question is *where*.
2. In Burp, **Proxy → HTTP history**, find the `POST /cart` request. Its body has `productId`, `quantity`, and a `price` parameter (in cents) sent straight from the browser.
3. Right-click → **Send to Repeater** (`Ctrl+R`).
4. In Repeater, change `price` from `133700` to something low like `1`. Click **Send**. The server echoes back the cart with the new price — no server-side validation rejected it.
5. Refresh `/cart` in the browser → the jacket shows the tampered price.
6. Place the order. It succeeds because it's now within the $100 credit. Lab solved.

## 4. Expected request/response (illustrative — not real evidence)

```
POST /cart HTTP/1.1
Host: <lab-id>.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

productId=1&redir=PRODUCT&quantity=1&price=1
```
Response: `302` back to the cart, now holding the item at the tampered price.

> Mark this block clearly as **illustrative**. Replace it with the real captured request in `evidence/` after you run the lab.

## 5. Root cause

The server uses a client-supplied value (`price`) as the source of truth for money. Violates **Complete Mediation** and the rule: never trust data only the client controls.

## 6. Defense (secure implementation)

- Never accept price/total from the request. Look the price up from the server's own database by `productId` on every request.
- Recompute subtotal, discount, and total server-side at checkout.
- See `naive_price_demo.py` for the smallest naive-vs-secure contrast.

## 7. Run the local demo

```powershell
python red_team/labs/lab1_client_side_trust/naive_price_demo.py
```
It shows the naive function trusting the client price, then the secure function ignoring it and using the catalog price.

## 8. Reusable SecureShop test case

- See [`secureshop_tests/test_cases/tc_t1_client_side_price.md`](../../secureshop_tests/test_cases/tc_t1_client_side_price.md).
- Related hypotheses: **H6** (price writable on Orders API), **H1** (checkout total trust).

## 9. Evidence to collect (manual)

Save under `evidence/lab1/`:
- Screenshot of the original rejected order.
- The captured `POST /cart` request showing the `price` parameter.
- The tampered Repeater request + response.
- The "lab solved" banner.
