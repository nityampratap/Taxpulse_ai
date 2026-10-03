# TAXPULSE AI — System Architecture

## Architecture Overview

TAXPULSE AI is built as a high-integrity, modular client-server application designed for automated tax compliance and reconciliation.

| Layer | Technology | Primary Role |
| :--- | :--- | :--- |
| **Frontend** | React 18 + Vite + TypeScript + Tailwind CSS + TanStack Query | Responsive controller dashboard, case management, and interactive discrepancy workbench. |
| **Backend** | FastAPI + SQLAlchemy ORM + Pandas + RapidFuzz + scikit-learn | High-throughput asynchronous REST API, reconciliation engine, and ML pipelines. |
| **Database** | PostgreSQL (Primary) / SQLite (Zero-config local fallback) | ACID-compliant relational persistence with strict decimal arithmetic and multi-tenancy. |
| **AI Copilot** | Groq (`llama-3.3-70b-versatile`) / Gemini / Mock Provider | Abstracted reasoning engine operating over isolated, structured JSON case payloads. |
| **Messaging** | Meta WhatsApp Cloud API / Webhook Simulator | Urgent alert dispatch and secure two-way human confirmation channel. |

---

## 1. System Component Layout

| Component | Modules & Paths | Responsibilities |
| :--- | :--- | :--- |
| **Ingestion Engine** | `backend/app/services/ingest/` | Validates file formats (CSV, XLSX, PDF), detects encoding, chunks records into database batches. |
| **Normalization Engine** | `backend/app/services/normalize/` | Standardizes vendor names, invoice numbers, timestamps (UTC ISO-8601), and converts money to `Decimal(18, 4)`. |
| **Reconciliation Core** | `backend/app/services/reconcile/` | Executes multi-pass matching: deterministic exact, normalized, RapidFuzz fuzzy scoring, semantic embeddings, and 1:N / N:1 splits. |
| **Anomaly Engine** | `backend/app/services/anomaly/` | Runs `scikit-learn` `IsolationForest` on feature vectors combined with deterministic statutory variance rules. |
| **Risk Scorer** | `backend/app/services/risk/` | Evaluates the 6 stored risk factors (0–100) and assigns compliance tiers (LOW, MEDIUM, HIGH, CRITICAL). |
| **LLM Provider Layer** | `backend/app/services/ai/` | Unified provider interface (`BaseAIProvider`) supporting Groq, Gemini, and Mock implementations with zero DB access. |
| **WhatsApp Subsystem** | `backend/app/services/whatsapp/` | Handles outbound templates, inbound webhooks, state machine enforcement (`EXPLAIN`, `REVIEW`, `CONFIRM`), and HMAC verification. |
| **Audit Subsystem** | `backend/app/services/audit/` | Records immutable audit events on every transition with actor tracking and before/after state diffs. |

---

## 2. Multi-Tenancy & Data Isolation

| Property | Rule & Implementation |
| :--- | :--- |
| **Partitioning Key** | `organization_id` (UUID / Integer) exists on all 18 tables. |
| **Query Isolation** | Repository and service queries enforce `WHERE organization_id = :org_id` automatically via session tenancy filters. |
| **Authentication Binding** | JWT claims directly inject the verified `organization_id` into FastAPI request state (`request.state.org_id`). |

---

## 3. Security & Boundary Guardrails

| Boundary | Enforcement Mechanism |
| :--- | :--- |
| **Frontend Secrets** | Only publishable/anon keys prefixed with `VITE_` are exposed in frontend bundles. Backend secret keys are strictly restricted to the server environment. |
| **AI Context Isolation** | The AI engine never connects to the database or executes SQL. It receives only sanitised, pre-compiled JSON contexts. |
| **WhatsApp Action Guard** | WhatsApp messages can NEVER directly alter financial or accounting ledger records. They can only transition `cases.status` to `RESOLVED` after an explicit, time-limited `CONFIRM <CODE>` response. |
| **Precision Math** | Python `decimal.Decimal` and database `NUMERIC(18, 4)` are enforced universally to prevent floating-point drift. |
