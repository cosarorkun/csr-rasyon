# CSR Rasyon Hesaplayıcı

Beef cattle TMR (Total Mixed Ration) calculator with INRA-based performance estimation, branded **CSR — Concentrated Smart Ration**. Single-page web app, Turkish UI, designed for field salespeople. JWT login, saved-ration history (with customer attribution), and admin-only feed management.

- **Backend:** Python + FastAPI + SQLAlchemy (SQLite)
- **Frontend:** Single static HTML + vanilla JS (no build step)
- **Auth:** JWT (8-hour token), bcrypt password hashing
- **Deployment:** Railway (one-click from GitHub)

## Project layout

```
.
├── main.py            # FastAPI app: routes + schemas
├── data.py            # Seed feed data, INRA UFV/PDI matrices, DMI table
├── calculator.py      # Pure calculation + bilinear interpolation
├── database.py        # SQLAlchemy models, engine, idempotent migrations, seed
├── auth.py            # JWT + password hashing + auth dependencies
├── requirements.txt
├── Procfile           # web: uvicorn main:app --host 0.0.0.0 --port $PORT
├── runtime.txt        # python-3.12.3
└── static/
    ├── index.html     # Login + main app (calc, history, admin) + edit feed modal
    └── csr-logo.png   # CSR logo (used in login, header, footer)
```

## Seeded users (created only on first DB init)

| Kullanıcı | Şifre | Rol |
|---|---|---|
| `sezer.karabulut` | `SezerCsrRasyon2026.` | Saha |
| `emre.basar` | `EmreCsrRasyon2026.` | Saha |
| `ayhan.cosar` | `26051108Ac.` | Yönetici |

Existing users in your live Railway DB are **never reset** — seeding only runs when the `users` table is empty.

## Schema migrations

`database._run_migrations()` runs idempotently on every startup. Currently applied:

- `saved_rations.customer_name` — added if missing on existing DBs (`ALTER TABLE saved_rations ADD COLUMN customer_name VARCHAR`).

Existing saved rations get `customer_name = NULL` and continue to work.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000

## API

All endpoints below require `Authorization: Bearer <token>` except `GET /` and `POST /auth/login`.

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/` | public | Serves `static/index.html` |
| POST | `/auth/login` | public | Body: `{username, password}` → `{access_token, is_admin, username}` |
| GET | `/auth/me` | user | Current user info |
| GET | `/feeds` | user | Full feed list (system + custom) and breeds — needed for the dropdown |
| POST | `/feeds` | **admin** | Add a custom feed |
| PUT | `/feeds/{id}` | **admin** | Update a custom feed; system feeds are read-only |
| DELETE | `/feeds/{id}` | **admin** | Delete a custom feed; system feeds protected |
| POST | `/calculate` | user | Run a TMR calculation |
| POST | `/rations` | user | Save (`customer_name` field included) |
| GET | `/rations` | user | List own; admins see all with `username` per row |
| DELETE | `/rations/{id}` | user | Own only; admin can delete any |

## Permission model

| Capability | Saha | Yönetici |
|---|---|---|
| Calculate ration | ✅ | ✅ |
| Save ration with `customer_name` | ✅ | ✅ |
| See own saved rations | ✅ | ✅ |
| See all users' saved rations | ❌ | ✅ |
| See per-ingredient detail table | ❌ | ✅ |
| Yönetim tab visible | ❌ | ✅ |
| Add / edit / delete custom feed | ❌ | ✅ |
| Edit or delete system feed | ❌ | ❌ (protected) |

Server-side checks via `get_current_admin` enforce all admin-only endpoints — frontend hiding is purely cosmetic.

## Deployment to Railway

1. Push to GitHub. Railway auto-builds on push.
2. **Environment variables:**
   - `DOYA_DB_PATH=/data/rasyon.db` (mount your volume at `/data`)
   - `DOYA_SECRET_KEY=<long random string>` — JWT signing key
3. **Volume:** mount path `/data`, so the SQLite file persists across redeploys.
4. Procfile starts the app: `uvicorn main:app --host 0.0.0.0 --port $PORT`.

The new `customer_name` column is added by the startup migration on the very first request after deploy — no manual SQL needed.

## Calculation overview

1. **Per ingredient:** `dm_kg = as_fed * dm_pct/100`, then UFV / PDIE / protein contributions on a DM basis.
2. **Totals + ratios:** UFV/kg DM, protein% DM, starch% DM (weighted on DM basis).
3. **Expected DMI:** % of body weight from `DMI_TABLE` (1.6% above 543.6 kg).
4. **Gain estimation:** bilinear interpolation in INRA UFV and PDI matrices. Final estimated gain = `min(UFV-limited, PDI-limited)` (limiting nutrient principle).
5. **INRA comparison** (only if target gain entered): required vs provided UFV/PDI with ✅/⚠️ indicators.

Display rounding: gain to nearest 10 g/day, UFV to 2 decimals, protein/starch to 1 decimal.
