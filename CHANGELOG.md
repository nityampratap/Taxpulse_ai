# Changelog

All notable changes to the TAXPULSE AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Fully wired `ExceptionDetailPage` with live case details, statutory calculation evidence, 6-factor risk matrix, AI Copilot root cause analysis, reviewer status transitions (`IN_REVIEW`, `RESOLVED`), and WhatsApp alert dispatch.
- Fully wired `WhatsAppPage` with live conversations stream and interactive inbound simulator supporting `EXPLAIN`, `REVIEW`, and guarded `CONFIRM` verification state machine.
- Fully wired `AuditPage` with live immutable append-only event stream, SHA-256 checksum rendering, and actor identification.
- Fully wired `ReconciliationPage` with live execution run history and trigger run pipeline action.
- Fully wired `TransactionsPage`, `VendorsPage`, and `TaxIntelligencePage` to live backend data endpoints.

### Fixed
- Fixed React minified error #31 on `ExceptionsPage` by safely handling nested vendor object shapes from the API.
- Fixed SPA fallback routing in `backend/app/main.py` to allow `/api/*` routes to correctly return 404 instead of serving `index.html`.
- Fixed `ReconciliationRun` foreign key purge on demo reset in `backend/app/api/v1/routers/demo.py` and `scripts/generate_demo_data.py`.
- Fixed dashboard empty state to be data-aware (3 states: no data -> generate, data loaded -> run reconciliation, reconciled with 0 cases -> no discrepancies).
- Created foundational product specification (`docs/PRODUCT_SPEC.md`) defining the 8-stage pipeline, hybrid intelligence architecture, and 6-factor risk scoring model.
- Created system architecture document (`docs/ARCHITECTURE.md`) detailing frontend, backend, database dialects, and security guardrails.
- Defined complete multi-tenant relational schema (`docs/DATA_MODEL.md`) covering all 18 tables with strict `NUMERIC(18, 4)` precision.
- Authored REST API specification (`docs/API_SPEC.md`) spanning 16 endpoint groups and standard error schema.
- Formatted canonical demo walkthrough (`docs/DEMO_FLOW.md`) detailing case `TX-10482` ($450 tax variance, score 62.00, WhatsApp flow).
- Outlined 20-phase implementation plan (`docs/IMPLEMENTATION_PLAN.md`) with explicit engineering checklists per phase.
- Documented initial Architecture Decision Records ADR-001 through ADR-008 (`docs/DECISIONS.md`).
- Initialized git repository, `.gitignore`, `.env.example`, and environment credentials.
- Scaffolded `frontend/` with Vite + React 19 + TypeScript + Tailwind CSS + TanStack Query + React Router + Recharts + Lucide Icons.
- Mapped DESIGN.md tokens into `tailwind.config.js`.
- Implemented `AppLayout` (10 nav items, top bar) and shared components (`DataTable`, `StatCard`, `StatusChip`, `RiskChip`, `EmptyState`, `ErrorState`, `Skeleton`, `MoneyText`).
- Built `apiClient.ts` with typed error handling and configurable base URL.
- Configured routes (`/login`, `/dashboard`, `/reconciliation`, `/transactions`, `/exceptions`, `/exceptions/:id`, `/tax-intelligence`, `/vendors`, `/reports`, `/whatsapp`, `/audit`, `/settings`) with loading/empty states.
- Added and verified Vitest smoke test suite passing 12/12 route render tests and clean build.
- Scaffolded `backend/` with FastAPI, pydantic-settings config (SQLite default), CORS restricted to `FRONTEND_ORIGIN`, and secret-redacting `RequestIdMiddleware`.
- Implemented consistent error handlers returning `{error:{code,message,details}}`.
- Built `/api/health` and `/api/health/ready` endpoints, and stubbed all 14 router groups per `API_SPEC.md` returning 501.
- Created `backend/pyproject.toml` and `backend/Dockerfile`.
- Added pytest test suite with 6 test cases verifying health endpoints, 501 stubs, and secret redaction.
- Implemented SQLAlchemy 2.0 models for all 18 tables with `Numeric(18, 2)` monetary columns, indexed `organization_id`, and documented indices.
- Configured Alembic with `render_as_batch=True` for SQLite/Postgres dual-engine support and created initial migration `4185da0ca3a3_create_initial_schema.py`.
- Added database seed command (`app.db.seed`) establishing demo tenant, 4 demo users (admin, accountant, reviewer, viewer), and demo tax rules.
- Added pytest tests for Alembic upgrade/downgrade migration cycles and model CRUD operations (all 9 tests passing).
- Added `backend/scripts/generate_demo_data.py` with fixed seed 42, deterministic anchoring to 2026-03-15, exact category count injections (100 base + 5 duplicates = 105 invoices), and pinned tax discrepancy case `TX-10482`.
- Exported ground truth fixtures to `backend/tests/fixtures/expected_results.json`.
- Implemented `POST /api/demo/generate` and `POST /api/demo/reset` endpoints with SQLite fallback and foreign key safety.
- Integrated "Generate demo data" action into frontend Dashboard empty state via `apiClient`.
- Implemented reconciliation engine with exact, normalized ID, RapidFuzz fuzzy ID, context-aware, split 1:N and N:1 matching passes, statutory tax rate verification, and strict status priority (`backend/app/services/reconciliation/`).
- Built deterministic anomaly detection engine with 8 statistical rule signals plus IsolationForest outlier scoring (`backend/app/services/anomaly/`).
- Implemented 6-factor risk scoring engine calibrated to enterprise thresholds (0-100 score, LOW/MEDIUM/HIGH/CRITICAL tiers) (`backend/app/services/risk/`).
- Implemented case lifecycle management service with state machine validation and role-based permissions (`backend/app/services/cases/`).
- Built AI Copilot service supporting Groq, Gemini, and deterministic template fallback with zero-hallucination number grounding checks (`backend/app/services/ai/`).
- Implemented WhatsApp alert dispatcher and command router supporting HELP, SUMMARY, CRITICAL, EXPLAIN, CASE, REVIEW, CONFIRM, and CANCEL with 10-minute expiry (`backend/app/services/whatsapp/`).
- Built SHA-256 immutable, tamper-evident audit logging service (`backend/app/services/audit/`).
- Wired all 16 FastAPI routers replacing 501 stubs with live database queries and business logic (`backend/app/api/v1/routers/`).
- Built CSV and XLSX streaming report exports with formula injection escaping (`backend/app/api/v1/routers/reports.py`).
- Added Alembic migration `d182e951d200_enable_row_level_security.py` enabling RLS across all 18 PostgreSQL tables.
- Authored WhatsApp Cloud API live deployment runbook (`docs/WHATSAPP_LIVE.md`) and raw payload fixtures (`docs/whatsapp_fixtures/`).
- Created system readiness doctor `scripts/check_env.py` verifying DB, JWT, AI, and WhatsApp configurations.
- Added comprehensive test suites: `test_tax.py`, `test_risk.py`, `test_ai.py`, `test_whatsapp.py`, and `test_integration_demo.py` (26/26 backend tests passing).
- Built synthetic evaluation script `backend/scripts/evaluate.py` demonstrating 100% recall across all 12 synthetic injection categories.
- Created cross-platform demo reset automation (`scripts/demo_reset.py` and `scripts/demo_reset.sh`) verifying canonical case `TX-10482`.
- Authored production multi-stage `Dockerfile`, `docker-compose.yml`, and enterprise `README.md`.
