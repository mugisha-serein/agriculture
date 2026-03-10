# Agriculture Backend

Modular monolith Django backend for the AgriMarket platform.

**Stack**
- Python 3.12+
- Django 6.0.2
- Django REST Framework 3.16.1
- djangorestframework-simplejwt 5.5.1
- PostgreSQL (required)

**Architecture**
Single deployable backend with strict app boundaries.

| App | Responsibility | Primary Tables |
|---|---|---|
| `users` | Identity, auth, sessions, JWT lifecycle | `users`, `sessions`, `refresh_tokens` |
| `verification` | KYC submission and admin verification workflow | `user_verifications` |
| `listings` | Marketplace crops and product listings | `crops`, `products` |
| `discovery` | Search, ranking, and home content | `search_queries` |
| `orders` | Order lifecycle and line-item allocation | `orders`, `order_items` |
| `payments` | Payment initiation and escrow flow | `payments`, `escrow_transactions` |
| `logistics` | Shipment coordination and tracking | `shipments` |
| `reputation` | Reviews, ratings, Bayesian reputation aggregation | `reviews` |
| `audit` | Immutable mutation audit + managed request action audit | `audit_events`, `audit_request_actions` |
| `dashboard` | Role-specific analytics and activity | Derived analytics |

**Hard Requirements**
- PostgreSQL is mandatory.
- `POSTGRES_DRIVER` must be `psycopg2`.
- `psycopg2-binary` must be importable in the Python environment.
- SQLite is not supported.

**Environment Variables**
`core/settings.py` loads variables from `.env` and the process environment.

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

**Setup**
```powershell
cd backend
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

**Docker**
From repo root:
```powershell
docker-compose up --build
```

**API Route Index**
Base route prefixes are configured in `core/urls.py`.

Identity `/api/identity/`
- `POST register/`
- `POST activate/`
- `POST login/`
- `POST refresh/`
- `POST logout/`
- `POST verify/`

Verification `/api/verification/`
- `POST submit/`
- `GET me/`
- `GET admin/pending/`
- `POST admin/<verification_id>/review/`

Marketplace `/api/marketplace/`
- `GET,POST crops/`
- `GET,POST products/`
- `GET products/me/`
- `GET,PATCH,DELETE products/<product_id>/`

Discovery `/api/discovery/`
- `GET search/`
- `GET home/`

Orders `/api/orders/`
- `GET,POST /`
- `GET seller/`
- `GET <order_id>/`
- `POST <order_id>/confirm/`
- `POST <order_id>/cancel/`
- `POST <order_id>/items/<item_id>/fulfill/`

Payments `/api/payments/`
- `GET /`
- `POST initiate/`
- `POST webhooks/`
- `GET <payment_id>/`
- `POST <payment_id>/release/`
- `POST <payment_id>/refund/`

Logistics `/api/logistics/`
- `GET,POST shipments/`
- `GET shipments/<shipment_id>/`
- `POST shipments/<shipment_id>/assign/`
- `POST shipments/<shipment_id>/status/`
- `POST shipments/<shipment_id>/cancel/`
- `POST shipments/<shipment_id>/confirm-delivery/`

Reputation `/api/reputation/`
- `POST reviews/`
- `GET users/<user_id>/reviews/`
- `GET users/<user_id>/summary/`
- `GET leaderboard/`

Audit `/api/audit/`
- `GET events/`
- `GET actions/`
- `POST actions/<action_id>/manage/`

Dashboard `/api/dashboard/`
- `GET stats/`

**Auditability Model**
Two layers are implemented:
- Entity mutation audit (`audit_events`): immutable create/update/delete/custom events with before/after snapshots and hash chain.
- Request action audit (`audit_request_actions`): request metadata + status for critical domains.

**Planned Additions (Per App)**
- `users`: MFA, passwordless auth, profile avatars
- `verification`: document storage, automatic OCR checks
- `listings`: product media galleries, inventory synchronization
- `discovery`: personalized ranking and saved searches
- `orders`: returns workflow, partial fulfillment tracking
- `payments`: external provider integrations, reconciliation tooling
- `logistics`: GPS tracking, route optimization
- `reputation`: badges, dispute resolution hooks
- `audit`: export pipelines and alerting
- `dashboard`: admin analytics and marketplace KPIs
