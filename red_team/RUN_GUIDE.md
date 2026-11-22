# RUN GUIDE — commands explained, step by step

Run every command from the project root (the folder with `docker-compose.yml`
and `manage.py` in it), unless a step says otherwise. Each command below says
what it does, what you should see, and what a bad result looks like.

---

## 1. Start SecureShop (needs Docker Desktop running)

```
docker compose -f docker-compose.yml -f red_team/docker-compose.override.yml up -d --build --wait
```

**What this does:** builds and starts three containers — `db` (PostgreSQL),
`web` (the Django app), and `nginx` (HTTPS front door). The `red_team/`
override file works around two bugs in the Blue Team's own scripts
(`scripts/generate_certs.sh` and `docker-entrypoint.sh` were saved with
Windows line endings, which crash on Linux) — it does this without changing
any of their files.

**What you should see:** after a minute or two, `docker compose ps` shows all
three containers as `healthy` or `running`.

**Database ports:** the Red Team override removes PostgreSQL's host port
binding, avoiding occupied or reserved Windows ports such as 5432. No
`POSTGRES_PORT` setting is needed. Django still connects internally to
`db:5432`. For database access, use `docker compose exec db psql -U nexus -d nexus`
(adjust the user and database if you configured different names).
The override requires Docker Compose 2.24.0 or newer for `!reset` support.

**Confirm it's actually up:**
```
curl -k https://localhost/
```
A `302` redirect to `/dashboard/` means it's working. `curl -k` skips the
browser's certificate warning — only use `-k` for this local self-signed
cert, never for a real site.

**To open it in an actual browser:** go to `https://localhost/` and click
through the "not secure" / "proceed anyway" warning once. This is expected —
it's a self-signed certificate generated locally for this assignment, not a
real certificate authority.

---

## 2. Re-run the live SecureShop regression tests

```
python red_team/live_tests/run_regression.py
```

**What this does:** logs in as the seeded `customer` account, then actually
exercises each defense — reads another user's order ID directly, tries to
set a custom price as a non-staff user, replays a blacklisted token, sends
7 bad logins in a row, and so on — and checks the *real* outcome (who owns
the data returned, what the server actually did), not just the HTTP status
code.

**What you should see:** a line per test ending in `TESTED - DEFENSE HELD`.
If any line says `CONFIRMED VULNERABILITY`, that's a real, live finding —
write it up using `reports/findings_template.md` before you do anything else.

**Output file:** `red_team/evidence/live/regression_results.md` gets
overwritten with the fresh run.

---

## 3. Re-run the Naive Shop attacks (no Docker needed)

```
python naive_shop/app.py
```
Leave that running in one terminal. In a second terminal:
```
python red_team/live_tests/attack_naive.py
```

**What this does:** the Naive Shop is a tiny insecure demo app (pure Python,
no dependencies) that deliberately has the same 7 flaws SecureShop defends
against. The attack script logs in, tampers with price, reuses a coupon,
reads another user's order, and so on, and prints `CONFIRMED VULNERABILITY`
for each — proving the *attack itself* works when the defense is absent,
which is the baseline the Blue Team's defenses are compared against.

**Output file:** `red_team/evidence/naive_shop/attack_results.md`.

Stop the naive shop afterwards (Ctrl+C in its terminal) — it must never be
exposed outside localhost.

---

## 4. Re-run static analysis

```
pip install bandit pip-audit --break-system-packages
bandit -r . -x "./.venv,./.git,./red_team,./naive_shop,./certs,./docs" -f json -o red_team/reports/bandit_results.json
pip-audit -r requirements.txt --format json -o red_team/reports/pip_audit.json
```

**Bandit** reads the Python source for risky patterns (hardcoded secrets,
unsafe `eval`, etc.) — it does **not** run the app, so a Bandit finding is
not proof of a live exploit; always read the flagged line yourself before
writing it up as a finding.

**pip-audit** checks `requirements.txt` against the public vulnerability
databases for each pinned version — it tells you what's outdated, not
whether the outdated part is actually reachable in this app.

---

## 5. Rebuild the reports (HTML + PDF)

```
pip install markdown weasyprint --break-system-packages
python red_team/reports/build_reports.py
```

This regenerates every file in `red_team/reports/html/` and the index at
`red_team/reports/index.html` from the `.md` source files — so edit the
`.md` file, never the generated `.html` directly.

Then generate PDFs from the HTML (WeasyPrint, cross-platform):
```python
import pathlib
from weasyprint import HTML
for f in sorted(pathlib.Path("red_team/reports/html").glob("*.html")):
    HTML(filename=str(f)).write_pdf(f"red_team/reports/pdf/{f.stem}.pdf")
```
Save that as a `.py` file and run it, or run it inline with `python -c "..."`.

If you're on Windows and prefer Edge instead of installing WeasyPrint, the
original `build_reports.bat` (Edge headless) still works the same way — just
make sure the `html/` files exist first.

**Always spot-check at least one PDF after rebuilding** — open it and look at
the actual cover page and one table, don't just check that the command
exited without an error. (A real bug — an invisible title on every cover
page — was only caught this way, not by the build succeeding silently.)

---

## 6. Tear down

```
docker compose down
```
Stops and removes the containers. The database volume persists unless you
add `-v`; add `-v` only if you want a completely clean reset.

---

## 7. If something in this guide doesn't match what you see

Don't force it to match — write down the actual command, the actual output,
and what you expected instead, in `reports/project_architecture.md` under a
"Blockers" note. A documented mismatch is worth more to your grade than a
report that quietly papers over one.
