# DOYA Besi Rasyon Hesaplayıcı

Beef cattle TMR (Total Mixed Ration) calculator with INRA-based performance estimation. Single-page web app, Turkish UI, designed for field salespeople. Includes JWT login, saved-ration history, and admin-managed custom feeds.

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
├── database.py        # SQLAlchemy models, engine, init/seed
├── auth.py            # JWT + password hashing + auth dependencies
├── requirements.txt
├── Procfile           # web: uvicorn main:app --host 0.0.0.0 --port $PORT
├── runtime.txt        # python-3.12.3
└── static/
    └── index.html     # Full UI (login, calc, history, admin)
```

## Seeded users (created on first startup)

| Kullanıcı | Şifre | Rol |
|---|---|---|
| `sezer.karabulut` | `SezerCsrRasyon2026.` | Saha |
| `emre.basar` | `EmreCsrRasyon2026.` | Saha |
| `ayhan.cosar` | `26051108Ac.` | Yönetici |

Passwords are hashed with bcrypt; the plaintext values above are only used during the one-time seed and to share with users.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000. The SQLite file `rasyon.db` is created in the working directory on first start and seeded automatically.

## API

All endpoints below require `Authorization: Bearer <token>` except `GET /` and `POST /auth/login`.

| Method | Path | Notes |
|---|---|---|
| GET | `/` | Serves `static/index.html` (public) |
| POST | `/auth/login` | Body: `{username, password}` → `{access_token, is_admin, username}` (public) |
| GET | `/auth/me` | Current user info |
| GET | `/feeds` | Full feed list (seeded + custom) and breeds |
| POST | `/feeds` | **Admin only.** Add a custom feed |
| DELETE | `/feeds/{id}` | **Admin only.** Delete a custom feed (system feeds protected) |
| POST | `/calculate` | Run a TMR calculation |
| POST | `/rations` | Save a calculated ration |
| GET | `/rations` | List saved rations (own; admins see all) |
| DELETE | `/rations/{id}` | Delete a ration (own; admins can delete any) |

## Deployment to Railway

1. Push this repo to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Select this repo. Railway auto-detects Python via `requirements.txt` and uses the `Procfile` to start the app.
4. **Recommended environment variables:**
   - `DOYA_SECRET_KEY` – any long random string. Used to sign JWTs. If unset, a built-in default is used (do change it).
   - `DOYA_DB_PATH` – defaults to `./rasyon.db`. Override only if you mount the volume to a different path.
5. **Persisting the SQLite file across deploys (important):**
   - In Railway, open the service → **Volumes** → **New Volume**.
   - Mount path: `/data`. Set env var `DOYA_DB_PATH=/data/rasyon.db`.
   - Without a volume, Railway preserves the file across restarts within a deployment but **wipes it on every redeploy**, meaning saved rations and any custom feeds you added would be lost on the next push.
6. Once the build finishes (~2 min), open the generated `*.up.railway.app` URL.

If Railway asks for the start command explicitly: `uvicorn main:app --host 0.0.0.0 --port $PORT`.

## Calculation overview

1. **Per ingredient:** `dm_kg = as_fed * dm_pct/100`, then UFV / PDIE / protein contributions on a DM basis.
2. **Totals + ratios:** UFV/kg DM, protein% DM, starch% DM (weighted on DM basis).
3. **Expected DMI:** % of body weight from `DMI_TABLE` (1.6% above 543.6 kg).
4. **Gain estimation:** bilinear interpolation in the INRA UFV and PDI matrices. Final estimated gain = `min(UFV-limited, PDI-limited)` (limiting nutrient principle).
5. **INRA comparison** (only if target gain entered): required vs provided UFV/PDI with ✅/⚠️ indicators.

All displayed values are rounded: gain to nearest 10 g/day, UFV to 2 decimals, protein/starch to 1 decimal.
