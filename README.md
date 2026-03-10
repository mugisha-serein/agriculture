# AgriMarket

End-to-end agriculture marketplace platform with a Django modular-monolith backend and a React + Vite frontend. Buyers discover verified listings, sellers manage products and orders, transporters handle shipments, and the system tracks reputation, escrow payments, and audit trails.

**Stack**
- Backend: Django 6, Django REST Framework, PostgreSQL
- Frontend: React 18, TypeScript, Vite
- Auth: JWT (access/refresh)
- Infrastructure: Docker, docker-compose

**Repository Structure**
- `backend/` Django modular monolith
- `frontend/` React app
- `docker-compose.yml` Local dev orchestration

**Quick Start (Docker)**
```powershell
# From repo root
# Ensure backend/.env exists (copy from backend/.env.example)
docker-compose up --build
```

**Local Dev (No Docker)**
Backend:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install psycopg2-binary
python manage.py migrate
python manage.py runserver
```

Frontend:
```powershell
cd frontend
npm install
npm run dev
```

**Environment**
- Backend reads `backend/.env`
- Frontend reads `VITE_API_URL` (default: `http://localhost:8000/api`)

**Documentation**
- Backend details: [backend/README.md](backend/README.md)
- Frontend details: [frontend/README.md](frontend/README.md)

**Planned Additions (High-Level)**
- Seller media galleries, buyer favorites, and saved searches
- Logistics GPS tracking and route optimization
- Payments provider integrations and escrow reconciliation tools
- Admin console for verification queues and audit exports
- Notification service (email/SMS/in-app)
