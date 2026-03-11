# Agriculture Backend

Modular monolith Django backend for the AgriMarket platform.

**Stack**
- Python 3.12+
- Django 6.0.2
- Django REST Framework 3.16.1
- djangorestframework-simplejwt 5.5.1
- PostgreSQL (required)
- Django-Q2 (async tasks)

**Architecture**
Single deployable backend with strict app boundaries and immutable audit capabilities.

| App | Responsibility | Primary Models / Systems |
|---|---|---|
| `users` | Identity, RBAC, Security | `User`, `Role`, `UserDevice`, `LoginVerification`, `LoginAttempt`, `IpReputation`, `LoginRateLimit` |
| `verification` | KYC & Compliance | `UserVerification`, `VerificationDocument`, `VerificationSelfie`, `VerificationReview`, `VerificationStatusLog`, `VerificationFraudCheck` |
| `listings` | Marketplace Catalog | `Product`, `ProductInventory`, `ProductMedia`, `ProductPricing`, `Crop` |
| `discovery` | Search & Ranking | Algorithms for relevance and marketplace discovery |
| `orders` | Order Lifecycle | `Order`, `OrderItem` (line-item allocation) |
| `payments` | Financial Operations | `Payment` aggregate, `EscrowTransaction` (immutable ledger) |
| `logistics` | Shipment Tracking | `Shipment` (assignment, tracking, proof of delivery) |
| `reputation` | Trust & Safety | `Review` (Bayesian reputation aggregation) |
| `audit` | System Observability | `AuditEvent` (immutable mutations), `AuditRequestAction` (managed actions) |
| `dashboard` | Analytics | Role-specific derived analytics and marketplace KPIs |

**Security & Data Integrity**
- **Identity Security**: Brute-force protection, account anomaly detection (device/IP tracking), HIBP password breach checks, and global rate limiting.
- **RBAC**: Granular role-based access control with dedicated roles for Buyers, Sellers, Transporters, and Admins.
- **Immutable Audit**: All domain mutations are hashed and chained in an immutable audit log.
- **Escrow Ledger**: Financial transactions are recorded in an immutable ledger with no deletion/modification allowed.

**Background Processing**
Asynchronous tasks (OCR, Face Matching, Fraud Detection) are handled by **Django-Q2**. Workers process intensive operations without blocking the request-response cycle.

**Hard Requirements**
- PostgreSQL is mandatory.
- `POSTGRES_DRIVER` must be `psycopg2`.
- `psycopg2-binary` must be importable in the Python environment.
- SQLite is not supported.

**Environment Variables**
| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Django signing secret |
| `DJANGO_DEBUG` | No | `true/false`, default `false` |
| `POSTGRES_DB` | Yes | PostgreSQL database name |
| `POSTGRES_USER` | Yes | PostgreSQL user |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `POSTGRES_HOST` | Yes | PostgreSQL host |
| `POSTGRES_PORT` | Yes | PostgreSQL port |
| `POSTGRES_DRIVER` | Yes | Must be `psycopg2` |
| `HIBP_ENABLED` | No | Enable HIBP password breach checks |
| `Q_CLUSTER_WORKERS` | No | Number of async worker processes (default 4) |

**Setup**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and set real credentials.

Apply migrations:
```powershell
python manage.py migrate
```

Start background workers:
```powershell
python manage.py qcluster
```

Run server:
```powershell
python manage.py runserver
```

**Docker**
```powershell
docker-compose up --build
```

**API Route Index**

| Domain | Base Path | Key Endpoints |
|---|---|---|
| **Identity** | `/api/identity/` | `register/`, `login/`, `verify/` (anomaly check), `refresh/`, `logout/` |
| **Verification** | `/api/verification/` | `submit/`, `me/`, `admin/pending/`, `admin/review/` |
| **Marketplace** | `/api/marketplace/` | `crops/`, `products/`, `products/me/`, `products/<id>/` |
| **Discovery** | `/api/discovery/` | `search/`, `home/` |
| **Orders** | `/api/orders/` | `POST /`, `GET seller/`, `<id>/confirm/`, `<id>/items/<id>/fulfill/` |
| **Payments** | `/api/payments/` | `initiate/`, `<id>/release/`, `webhooks/` |
| **Logistics** | `/api/logistics/` | `shipments/`, `shipments/<id>/assign/`, `confirm-delivery/` |
| **Reputation** | `/api/reputation/` | `reviews/`, `leaderboard/`, `users/<id>/summary/` |
| **Audit** | `/api/audit/` | `events/`, `actions/`, `actions/<id>/manage/` |
| **Dashboard** | `/api/dashboard/` | `stats/` |

