<div align="center">
  <h1>🌾 Agriculture Platform Backend</h1>
  <p>Enterprise-grade services orchestrating marketplace, logistics, trust, and compliance workflows.</p>
</div>

<p align="center">
  <span style="color:#005f73">Modern Django stack · Modular apps · Auditability-first</span>
</p>

---

## Core Responsibilities
| Domain | Responsibility |
| --- | --- |
| **Discovery** | Search telemetry, sorting analytics, and platform system registry for discovery experiences. |
| **Listings** | Marketplace catalog, pricing, inventory, and validation guards that keep offerings consistent. |
| **Orders** | Order creation, allocation, fulfillment, cancellation, and buyer/seller access controls with transactional safety. |
| **Payments** | Escrow ledger, refund controls, idempotency, and immutable financial transactions plus reconciliation hooks. |
| **Logistics** | Shipment lifecycle management, tracking, route planning, delivery telemetry, and transporter coordination. |
| **Reputation** | Review creation, Bayesian scoring, trust signals, badge awards, and anti-manipulation monitoring. |
| **Users** | Identity, RBAC, device registration, anomaly detection, and secure authentication policies. |
| **Verification** | KYC workflow modeling, fraud signals, document/selfie management, and submission queues. |
| **Audit** | Immutable change events, request hashing, alerts, export pipelines, and project-wide observability. |
| **Dashboard** | Analytics engine aggregating warehouse metrics, marketplace health, and admin investigation panels. |

---

## Architectural Highlights
- **Hash-chained auditing:** Every model mutation and monitored API action includes deterministic SHA256 chaining plus alert/export surfaces for legal/compliance audiences.
- **Data warehouse tables:** Daily sales, per-product/seller/buyer performance snapshots enforce uniqueness and double as the analytics fuel for dashboards.
- **Enterprise dashboards:** Admin analytics cover fraud, verification backlogs, payment reconciliation, shipment delays, and seller health with live fallback metrics.
- **Multi-role coverage:** Sellers, transporters, and administrators receive tailored APIs (dashboards, telemetry, analytics) with role gating and reputation cues.
- **Normalization:** All apps use database constraints (`unique_together`, idempotent keys) to prevent duplicate artifacts while allowing auditability across domains.

---

## Quick Links
- `manage.py test orders logistics reputation audit dashboard` — comprehensive regression test sweep.
- `audit/` — immutable events, alerts, exports.
- `dashboard/` — analytics models + admin panels.
- `dashboard/api/analytics/` — admin-only insights endpoint.

---

## Developer Notes
> Keep new schemas connected to the audit hash chain and ensure signal-based logging remains consistent when you introduce new models.

Stay professional, keep duplicates normalized, and treat every API as a product-grade contract.
