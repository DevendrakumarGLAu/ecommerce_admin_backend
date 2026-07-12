# Firozabad Bangles — E-commerce Backend

A production-oriented REST API for a multi-admin e-commerce catalog, built with **FastAPI** and **SQLAlchemy 2.0 (async)**. It serves both the **admin panel** (Angular) and the **buyer-facing storefront** (Angular SSR) from a single backend.

## Tech stack

| Concern | Choice |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Migrations | Alembic |
| Database | PostgreSQL (Supabase-hosted or self-managed) |
| Cache / rate limiting | Redis, with an in-memory fallback (`USE_REDIS=false`) for local dev |
| Auth | JWT access/refresh tokens (python-jose), bcrypt password hashing (passlib) |
| File storage | Supabase Storage (S3-compatible REST API, no SDK dependency) |
| Validation | Pydantic v2 |

## Architecture

Each domain follows the same layered shape:

```
app/api/<domain>.py            → FastAPI routes, request/response wiring, auth dependencies
app/services/<domain>_service.py → business logic, authorization checks, cache invalidation
app/repositories/<domain>_repository.py → SQLAlchemy queries
app/models/<domain>.py         → ORM models
app/schemas/<domain>.py        → Pydantic request/response schemas
```

Every endpoint responds with the same envelope:

```json
{ "success": true, "message": "...", "data": { ... } }
```

Paginated list endpoints nest `{ items, page, limit, total, pages }` inside `data`.

## Roles & authorization

Three roles: `super_admin`, `admin`, `customer`.

- **`super_admin`** — sees and manages the entire product catalog, and can promote/demote other users' roles (`PATCH /users/{id}/role`). Cannot change their own role (avoids self-lockout).
- **`admin`** — a per-seller account. `GET /products?mine=true` scopes results to products they created. Legacy products with no owner (`created_by IS NULL`) are visible to every admin until one of them edits it, at which point they become its owner. Regular admins can only update/delete/attach media to products they own.
- **`customer`** — public storefront account (cart, wishlist).

There is no invite/approval flow. `POST /auth/register-admin` always creates a plain `admin` account — the **only** way to create the first `super_admin` is the seed script below.

## Getting started

```bash
cd ecommerce-backend
python -m venv venv
venv\Scripts\activate            # Windows; use `source venv/bin/activate` on macOS/Linux

pip install -r requirements.txt

copy .env.example .env           # then fill in real values (see below)

alembic upgrade head

# create your first super admin (only way to bootstrap one)
python scripts/seed_admin.py --role super_admin --email you@example.com --password "ChangeMe123"

uvicorn app.main:app --reload --port 8000
```

Interactive API docs: `http://localhost:8000/docs` (Swagger) or `/redoc`.

### Required environment variables (`.env`)

| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `SECRET_KEY` | Long random string for JWT signing |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET` | Needed for image/video uploads |
| `USE_REDIS` | `false` (default) uses an in-process in-memory cache — zero external dependencies for local dev. Set `true` + a real `REDIS_URL` once Redis is provisioned; caveat: cache/rate-limit/token-blacklist state resets on every restart and isn't shared across multiple workers while `USE_REDIS=false`. |
| `FRONTEND_URL` | Comma-separated CORS allow-list, e.g. `http://localhost:4200,http://localhost:4500` |

See `.env.example` for the full list (upload size limits, rate limit, etc.).

### Seeding accounts

```bash
# a regular admin (seller)
python scripts/seed_admin.py --email seller@example.com --password "ChangeMe123"

# the super admin (only way to get one — no API endpoint for it)
python scripts/seed_admin.py --role super_admin --email owner@example.com --password "ChangeMe123"
```

Safe to re-run — if the email already exists it just reports that instead of duplicating.

## Domains / feature surface

- **Auth** — register (customer), register-admin, login, refresh (with rotation + blacklist), logout, me, update profile, change password, OTP-based forgot/reset password (see below).
- **Products** — full CRUD, per-admin ownership scoping, search/filter/sort, multi-image gallery, multi-video gallery, marketplace "buy it here" links (Amazon/Flipkart/Meesho/Myntra/Snapdeal/Other), draft/published/archived status, featured/bestseller/new-arrival flags.
- **Categories** — CRUD, `is_active` (paused categories stay in the admin panel but can be hidden from the storefront), SEO fields.
- **Cart / Wishlist** — per-customer.
- **Uploads** — `POST /uploads/image`, `POST /uploads/video` — validates size/content-type, streams to Supabase Storage.
- **Settings** — single-row site config: branding (logo/favicon), homepage hero banner (image + optional title/subtitle override), contact info, social links, analytics IDs. Public `GET`, admin-only `PUT`.
- **Users** — admin-facing list/view/activate/deactivate; super-admin-only role changes.
- **Dashboard** — aggregate stats for the admin panel.

## Forgot-password (OTP) flow

A 6-digit OTP is generated, hashed, and stored server-side, then emailed via **Gmail SMTP with an App Password** — no paid or third-party email API. `OTP_DEBUG_MODE=true` additionally echoes the OTP in the API response, for testing without a working Gmail App Password on hand; leave it `false` (the default) once email delivery works.

### One-time Gmail setup

1. Turn on 2-Step Verification on the sending Gmail account: <https://myaccount.google.com/security>
2. Google Account → Security → **App passwords** → generate one (pick any name, e.g. "Firozabad Bangles backend").
3. In `.env`:
   ```
   SMTP_USERNAME=your-address@gmail.com
   SMTP_APP_PASSWORD=the-16-character-app-password
   ```
   (Spaces in the copy-pasted App Password are stripped automatically.) Never use your real Gmail account password here — App Passwords are revocable independently and are exactly what Google intends for this.

### Swapping providers later

Delivery is isolated behind one interface: `app/services/email/base.py:EmailProvider`. `GmailSMTPProvider` (`app/services/email/gmail_smtp_provider.py`) is the only implementation today. To move to SendGrid/SES/Postmark/etc., add a new `EmailProvider` subclass and change the one line in `app/services/email/__init__.py:get_email_provider()`. Neither `otp_notifier.py` nor `PasswordResetService` — nor any endpoint — needs to change.

A delivery failure (bad credentials, Gmail hiccup, network blip) is logged but doesn't fail the request — the OTP is already safely stored server-side by the time sending is attempted, so a transient email problem shouldn't turn into a 500 for a 3–4-user app where you'd rather just check the server logs.

### The three endpoints

**1. `POST /auth/forgot-password`**  `{ "email": "user@example.com" }`

- 404 if no account matches that email.
- Any OTP still outstanding for that user is invalidated (`is_used = true`) — only the newest one is ever valid.
- Generates a cryptographically random 6-digit code (`secrets.randbelow`, not `random`), hashes it with the same bcrypt helper used for passwords, and stores a new `password_reset_otps` row with a 5-minute `expires_at`.
- Response: `{ "message": "...", "expires_in_minutes": 5, "otp": "482913" }` — `otp` is `null` when `OTP_DEBUG_MODE=false`.

**2. `POST /auth/verify-otp`**  `{ "email": "...", "otp": "482913" }`

- 404 unknown email; 400 if there's no active OTP row.
- 400 if the OTP has expired (and the row is immediately marked used, so it can't be retried after the fact).
- 429 if the row has already hit `OTP_MAX_ATTEMPTS` (default 5) wrong guesses — forces a fresh `/forgot-password` call.
- 400 with a remaining-attempts count on a wrong code (and increments `attempts`).
- On a correct code: marks the row `is_verified = true` and issues a **second, unrelated secret** — a `reset_token` (`secrets.token_urlsafe(32)`, hashed before storage, 10-minute expiry) — returned as `{ "reset_token": "...", "expires_in_minutes": 10 }`. The OTP itself is never accepted again after this point.

**3. `POST /auth/reset-password`**  `{ "email": "...", "reset_token": "...", "new_password": "..." }`

- Requires an OTP row that is verified, unexpired, and whose `reset_token` hash matches — otherwise 400 (with distinct messages for "verify first", "expired", "invalid token").
- Hashes `new_password` with bcrypt and updates the user.
- Marks the OTP row `is_used = true` in the same transaction — it (and its reset token) can never be used again. Requesting a new OTP afterwards starts the flow over from a clean slate.

The existing global `RateLimitMiddleware` (per IP+path per minute) already covers these endpoints against request-flooding; the per-record `attempts` counter above additionally throttles OTP-guessing specifically.

### `password_reset_otps` table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → `users.id`, `ON DELETE CASCADE` |
| `otp_hash` | varchar(255) | bcrypt hash of the 6-digit code — the plaintext OTP is never persisted |
| `reset_token_hash` | varchar(255), nullable | bcrypt hash of the post-verification reset token; `null` until verified |
| `expires_at` | timestamptz | OTP expiry (issued-at + `OTP_EXPIRY_MINUTES`) |
| `reset_token_expires_at` | timestamptz, nullable | reset-token expiry (verified-at + `OTP_RESET_TOKEN_EXPIRY_MINUTES`) |
| `is_verified` | boolean | set once the correct OTP is supplied |
| `is_used` | boolean | set on successful reset, expiry, lockout, or superseding by a newer OTP request — once true, the row is dead |
| `attempts` | int | incorrect-OTP counter, reset by each new `/forgot-password` call |
| `created_at`, `updated_at` | timestamptz | standard mixin |

Nothing about this table is exposed to the client directly — every field is read/written only by `PasswordResetService`.

## Known gaps / things to know before relying on this

- No test suite yet.
- The admin panel's existing forgot/reset-password *screens* were built earlier for a link-based flow (`{ token, new_password }`, no OTP-entry step) and haven't been updated to the OTP flow (`email` + `otp` → `reset_token` → `email` + `reset_token` + `new_password`) implemented here — the API is ready, the UI isn't wired to it yet.
- This flow doesn't revoke existing login sessions (refresh-token blacklist) after a password reset — same as the existing `/auth/change-password` endpoint, which has the same gap. Worth adding to both if you want a reset to force logout everywhere.
- Product ownership claiming is "first admin to edit an unclaimed product owns it" — intentional for backward compatibility, but means an unclaimed catalog can be silently split across admins over time if that's not desired.
