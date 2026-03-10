# Agriculture Backend

Modular monolith Django backend for an agriculture marketplace MVP.

## Stack

- Python 3.13
- Django 6.0.2
- Django REST Framework 3.16.1
- djangorestframework-simplejwt 5.5.1
- PostgreSQL (required)
- psycopg2-binary (required by settings)

## Architecture

Single deployable backend with strict app boundaries.

| App | Responsibility | Primary Tables |
|---|---|---|
| `users` | Identity, auth, sessions, JWT lifecycle | `users`, `sessions`, `refresh_tokens` |
| `verification` | KYC submission and admin verification workflow | `user_verifications` |
| `listings` | Marketplace crops and product listings | `crops`, `products` |
| `discovery` | Search/filter/ranking over listings (no product duplication) | `search_queries` |
| `orders` | Order lifecycle and line-item allocation | `orders`, `order_items` |
| `payments` | Idempotent payment initiation and escrow flow | `payments`, `escrow_transactions` |
| `logistics` | Shipment coordination and tracking | `shipments` |
| `reputation` | Reviews, ratings, Bayesian reputation aggregation | `reviews` |
| `audit` | Immutable mutation audit + managed request action audit | `audit_events`, `audit_request_actions` |

## Hard Requirements

- PostgreSQL is mandatory.
- `POSTGRES_DRIVER` must be `psycopg2`.
- `psycopg2-binary` must be importable in the Python environment that runs Django.
- SQLite is not supported by `core/settings.py`.

## Environment Variables

`core/settings.py` loads variables from `.env` and process environment.

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Django signing secret |
| `DJANGO_DEBUG` | No | `true/false`, default `false` |
| `DJANGO_ALLOWED_HOSTS` | No | Comma-separated hosts |
| `POSTGRES_DB` | Yes | PostgreSQL database name |
| `POSTGRES_USER` | Yes | PostgreSQL user |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `POSTGRES_HOST` | Yes | PostgreSQL host |
| `POSTGRES_PORT` | Yes | PostgreSQL port |
| `POSTGRES_DRIVER` | Yes | Must be `psycopg2` |
| `POSTGRES_CONN_MAX_AGE` | No | DB persistent connection lifetime (seconds), default `60` |
| `POSTGRES_SSLMODE` | No | Optional PostgreSQL SSL mode |
| `JWT_ACCESS_MINUTES` | No | Access token lifetime in minutes, default `15` |
| `JWT_REFRESH_DAYS` | No | Refresh token lifetime in days, default `7` |

## PostgreSQL Provisioning

Run as PostgreSQL superuser:

```sql
CREATE ROLE agriculture_user WITH LOGIN PASSWORD 'replace_with_strong_password';
ALTER ROLE agriculture_user CREATEDB;

CREATE DATABASE agriculture OWNER agriculture_user;
GRANT ALL PRIVILEGES ON DATABASE agriculture TO agriculture_user;
```

Connect to the `agriculture` database and run:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

GRANT ALL ON SCHEMA public TO agriculture_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agriculture_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agriculture_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO agriculture_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO agriculture_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON SEQUENCES TO agriculture_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON FUNCTIONS TO agriculture_user;
```

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install psycopg2-binary
```

Create `.env` from `.env.example` and set real secrets/credentials.

Apply schema:

```powershell
python manage.py migrate
```

Run server:

```powershell
python manage.py runserver
```

## API Route Index

Base route prefixes are configured in [`core/urls.py`](core/urls.py).

### Identity

Prefix: `/api/identity/`

- `POST register/`
- `POST activate/`
- `POST login/`
- `POST refresh/`
- `POST logout/`
- `POST verify/`

### Verification

Prefix: `/api/verification/`

- `POST submit/`
- `GET me/`
- `GET admin/pending/`
- `POST admin/<verification_id>/review/`

### Marketplace

Prefix: `/api/marketplace/`

- `GET,POST crops/`
- `GET,POST products/`
- `GET products/me/`
- `GET,PATCH,DELETE products/<product_id>/`

### Discovery

Prefix: `/api/discovery/`

- `GET search/`

### Orders

Prefix: `/api/orders/`

- `GET,POST /`
- `GET seller/`
- `GET <order_id>/`
- `POST <order_id>/confirm/`
- `POST <order_id>/cancel/`
- `POST <order_id>/items/<item_id>/fulfill/`

### Payments

Prefix: `/api/payments/`

- `GET /`
- `POST initiate/`
- `POST webhooks/`
- `GET <payment_id>/`
- `POST <payment_id>/release/`
- `POST <payment_id>/refund/`

### Logistics

Prefix: `/api/logistics/`

- `GET,POST shipments/`
- `GET shipments/<shipment_id>/`
- `POST shipments/<shipment_id>/assign/`
- `POST shipments/<shipment_id>/status/`
- `POST shipments/<shipment_id>/cancel/`
- `POST shipments/<shipment_id>/confirm-delivery/`

### Reputation

Prefix: `/api/reputation/`

- `POST reviews/`
- `GET users/<user_id>/reviews/`
- `GET users/<user_id>/summary/`
- `GET leaderboard/`

### Audit

Prefix: `/api/audit/`

- `GET events/`
- `GET actions/`
- `POST actions/<action_id>/manage/`

## Auditability Model

Two layers are implemented:

- Entity mutation audit (`audit_events`):
  - Immutable create/update/delete/custom events
  - Before/after state snapshots and field-level change set
  - Hash chain (`previous_hash`, `event_hash`)
- Request action audit (`audit_request_actions`):
  - Captures action-level activity for monitored scopes:
    - `payments`, `orders`, `logistics`, `listings`, `verification`, `last_login`
  - Records actor/request/response metadata, duration, management status
  - Supports operational triage through `management_status` and `management_note`

## Test Execution

Run full suite:

```powershell
python manage.py test users.tests verification.tests listings.tests discovery.tests orders.tests payments.tests logistics.tests reputation.tests audit.tests -v 1
```

Run integrity checks:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Notes on `requirements.txt`

`requirements.txt` currently contains many packages unrelated to this backend runtime. For deployment hardening, split dependencies into:

- backend runtime requirements
- development/test requirements
- unrelated toolchain dependencies

Current backend runtime-critical packages include:

- `Django`
- `djangorestframework`
- `djangorestframework_simplejwt`
- `psycopg2-binary`
- `sqlparse`
- `tzdata`
