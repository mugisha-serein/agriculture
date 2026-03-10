# Agriculture Frontend

Buyer, seller, and transporter experiences built with React, TypeScript, and Vite.

**Stack**
- React 18
- TypeScript
- Vite
- Axios
- Lucide icons

**Getting Started**
```powershell
cd frontend
npm install
npm run dev
```

**Environment**
- `VITE_API_URL` (default `http://localhost:8000/api`)

**Docker**
From repo root:
```powershell
docker-compose up --build
```

**Project Structure**
- `src/pages/identity` Login, register, profile, verification
- `src/pages/marketplace` Discovery, listings, seller products, crops
- `src/pages/orders` Order history and details
- `src/pages/logistics` Shipments and tracking
- `src/pages/payments` Transactions
- `src/pages/reputation` Reviews and reputation
- `src/pages/dashboard` Seller/transporter dashboard
- `src/components` Shared layout, error boundary, UI helpers

**Runtime Behavior**
- JWTs stored in `sessionStorage`
- Centralized system error display via `SystemInlineError`
- Role-based access enforced in routing

**Planned Additions (Per App/Page)**
- `identity`: MFA flows, profile avatars, account recovery
- `marketplace`: saved searches, product media gallery, advanced filters
- `orders`: returns flow, buyer notifications, delivery confirmations
- `logistics`: live map tracking and driver status updates
- `payments`: payment method management and escrow status timeline
- `reputation`: richer review summaries and badges
- `dashboard`: custom KPIs per role and exportable reports
- `home`: dynamic hero media and admin-managed content
