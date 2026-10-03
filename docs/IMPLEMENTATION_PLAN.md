# TAXPULSE AI — 20-Phase Implementation Plan

## Overview
This document lays out the comprehensive 20-phase engineering roadmap for building TAXPULSE AI from initial repository foundations to complete production hardening.

---

### Phase 1: Environment & Project Scaffolding
- [ ] Initialize repository structure (`backend/`, `frontend/`, `docs/`)
- [ ] Validate Python 3.11+, Node.js 20+, and package managers
- [ ] Configure root configuration files (`.gitignore`, `.env.example`, `AGENTS.md`)
- [ ] Set up automated linting and formatting (Ruff, ESLint, Prettier)

### Phase 2: Database Layer & Dual Dialect Support
- [ ] Configure SQLAlchemy async/sync session management
- [ ] Implement database URL resolver (PostgreSQL primary with SQLite fallback)
- [ ] Set up Alembic migration framework
- [ ] Write integration test verifying cross-engine dialect compatibility

### Phase 3: Domain Models & Multi-Tenant Schema (18 Tables)
- [ ] Implement tenant-scoped base model enforcing `organization_id`
- [ ] Define core entities (`organizations`, `users`, `vendors`)
- [ ] Define document entities (`invoices`, `transactions`, `payments`, `ledger_entries`)
- [ ] Define workflow & audit entities (`tax_rules`, `import_batches`, `reconciliation_runs`, `reconciliation_results`, `anomalies`, `cases`, `case_assignments`, `audit_events`, `whatsapp_messages`, `pending_confirmations`, `ai_interactions`)
- [ ] Enforce `NUMERIC(18, 4)` Decimal constraints on all monetary columns

### Phase 4: Audit Logging & Immutability Engine
- [ ] Implement centralized `audit_service`
- [ ] Build SHA-256 state hashing utility for before/after record snapshots
- [ ] Enforce append-only table policies on `audit_events`
- [ ] Write tests verifying tamper-detection and hash verification

### Phase 5: Tax Rules Engine & Temporal Rate Evaluator
- [ ] Build `TaxRuleEngine` supporting jurisdictional rate lookups
- [ ] Implement temporal date range query (`effective_from <= date <= effective_to`)
- [ ] Create calculation validator for line-item tax vs expected statutory rate
- [ ] Unit test edge cases (rate transitions, leap years, missing rules)

### Phase 6: Ingestion Pipeline & File Parsers
- [ ] Implement CSV stream parser with header autodetection
- [ ] Implement Excel (.xlsx) workbook parser via Pandas/openpyxl
- [ ] Implement basic PDF structured invoice parser
- [ ] Enforce batch hash calculation and deduplication safeguards

### Phase 7: Document Normalization & Sanitization
- [ ] Implement alphanumeric invoice number sanitizer
- [ ] Build vendor name canonicalization using clean token dictionaries
- [ ] Enforce strict ISO-8601 UTC date parsing
- [ ] Standardize currency normalization and Decimal conversions

### Phase 8: Core Deterministic Reconciliation Engine
- [ ] Implement Pass 1: Exact reference and ID matching
- [ ] Implement Pass 2: Exact vendor + exact date + exact amount matching
- [ ] Implement Pass 3: Tolerance matching (configurable penny/cent boundaries)
- [ ] Persist match records in `reconciliation_results` with confidence scores

### Phase 9: Fuzzy & Semantic Reconciliation Engine
- [ ] Integrate `RapidFuzz` for normalized vendor name matching
- [ ] Implement Levenshtein distance matching for typo-prone invoice numbers
- [ ] Implement semantic embedding matcher for unstructured transaction descriptions
- [ ] Calibrate composite confidence scoring thresholds (0.0000 to 1.0000)

### Phase 10: 1:N and N:1 Split Reconciliation
- [ ] Build subset-sum search algorithm for one-to-many payments to single invoice
- [ ] Build many-to-one batch settlement reconciliation
- [ ] Implement greedy heuristic optimization for large split sets
- [ ] Write integration tests for complex split billing scenarios

### Phase 11: ML Anomaly Detection (IsolationForest)
- [ ] Implement feature extraction pipeline (amount z-score, date lag, tax ratio)
- [ ] Train/fit `scikit-learn` `IsolationForest` on baseline transaction profiles
- [ ] Combine ML anomaly scores with deterministic statutory red-flags
- [ ] Persist flags and feature vectors in `anomalies` table

### Phase 12: Stored Factor Risk Scoring Engine
- [ ] Implement factor computation service: Mismatch (25), Exposure (25), Tax (20), Anomaly (15), Vendor (10), Recurrence (5)
- [ ] Build classification mapper (LOW <30, MEDIUM 30-54, HIGH 55-74, CRITICAL >=75)
- [ ] Store immutable factor breakdown JSON in `cases.factor_breakdown`
- [ ] Verify test suite across all risk tiers

### Phase 13: Case Management & State Transition Machine
- [ ] Build `CaseService` with strict state machine (`OPEN` -> `IN_REVIEW` -> `RESOLVED` / `REJECTED`)
- [ ] Implement automated priority assignment and SLA calculation
- [ ] Implement reviewer assignment and escalation workflows
- [ ] Write state machine validation tests preventing illegal transitions

### Phase 14: LLM Copilot & Provider Abstraction
- [ ] Implement `BaseAIProvider` interface
- [ ] Build `GroqProvider` using Groq SDK / REST API
- [ ] Build `GeminiProvider` using Google GenAI SDK
- [ ] Build `MockAIProvider` operating over live database state
- [ ] Build prompt compiler injecting sanitized JSON context with zero DB access

### Phase 15: WhatsApp Channel & Two-Way Confirmation Engine
- [ ] Implement Meta WhatsApp Cloud API outbound client
- [ ] Build inbound webhook receiver with HMAC signature verification
- [ ] Implement state engine for `EXPLAIN`, `REVIEW`, and `CONFIRM <CODE>` commands
- [ ] Implement strict guardrail: WhatsApp can only change case status, NEVER ledger records
- [ ] Build `simulate-inbound` endpoint for local end-to-end testing

### Phase 16: Canonical Demo Data Generator (Case TX-10482)
- [ ] Build database seeder creating tenant, users, vendors, and rules
- [ ] Seed Case `TX-10482`: $100k invoice, $100k payment, $97.5k base @ 18% -> $17,550 expected vs $18,000 recorded
- [ ] Verify risk score precisely evaluates to `62.00` (`HIGH`)
- [ ] Create automated reset endpoint `POST /api/v1/demo/reset`

### Phase 17: FastAPI REST API Implementation
- [ ] Implement all 16 endpoint groups adhering to API specification
- [ ] Standardize error handlers returning `{ "error": { "code", "message", "details" } }`
- [ ] Configure CORS middleware and request ID tracking
- [ ] Write integration test suite covering all route handlers

### Phase 18: Frontend Foundation (React + Vite + Tailwind + TanStack Query)
- [ ] Initialize React 18 TypeScript application via Vite
- [ ] Configure Tailwind CSS with design tokens and status color mappings
- [ ] Set up TanStack Query client with caching and retry policies
- [ ] Build application shell: Top navigation, sidebar, notifications

### Phase 19: Frontend Reconciliation & Case Management Views
- [ ] Build Dashboard view with real-time metrics, risk distribution, and trends
- [ ] Build Reconciliation Workbench with side-by-side matching view
- [ ] Build Case Detail view showing risk breakdown, factor bars, and AI explanation drawer
- [ ] Build WhatsApp Simulator panel for live interactive demonstration

### Phase 20: End-to-End Verification & Production Readiness
- [ ] Run automated end-to-end test validating full pipeline (Ingest -> Audit)
- [ ] Execute canonical demo verification (`TX-10482`)
- [ ] Audit all endpoints for multi-tenant isolation and Decimal precision
- [ ] Document final operating procedures and sign off deployment checklist
