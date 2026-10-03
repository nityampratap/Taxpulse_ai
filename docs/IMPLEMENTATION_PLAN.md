# TAXPULSE AI — 20-Phase Implementation Plan

## Overview
This document lays out the comprehensive 20-phase engineering roadmap for building TAXPULSE AI from initial repository foundations to complete production hardening.

---

### Phase 1: Environment & Project Scaffolding
- [x] Initialize repository structure (`backend/`, `frontend/`, `docs/`)
- [x] Validate Python 3.11+, Node.js 20+, and package managers
- [x] Configure root configuration files (`.gitignore`, `.env.example`, `AGENTS.md`)
- [x] Set up automated linting and formatting (Ruff, ESLint, Prettier)

### Phase 2: Database Layer & Dual Dialect Support
- [x] Configure SQLAlchemy async/sync session management
- [x] Implement database URL resolver (PostgreSQL primary with SQLite fallback)
- [x] Set up Alembic migration framework
- [x] Write integration test verifying cross-engine dialect compatibility

### Phase 3: Domain Models & Multi-Tenant Schema (18 Tables)
- [x] Implement tenant-scoped base model enforcing `organization_id`
- [x] Define core entities (`organizations`, `users`, `vendors`)
- [x] Define document entities (`invoices`, `transactions`, `payments`, `ledger_entries`)
- [x] Define workflow & audit entities (`tax_rules`, `import_batches`, `reconciliation_runs`, `reconciliation_results`, `anomalies`, `cases`, `case_assignments`, `audit_events`, `whatsapp_messages`, `pending_confirmations`, `ai_interactions`)
- [x] Enforce `NUMERIC(18, 4)` Decimal constraints on all monetary columns

### Phase 4: Audit Logging & Immutability Engine
- [x] Implement centralized `audit_service`
- [x] Build SHA-256 state hashing utility for before/after record snapshots
- [x] Enforce append-only table policies on `audit_events`
- [x] Write tests verifying tamper-detection and hash verification

### Phase 5: Tax Rules Engine & Temporal Rate Evaluator
- [x] Build `TaxRuleEngine` supporting jurisdictional rate lookups
- [x] Implement temporal date range query (`effective_from <= date <= effective_to`)
- [x] Create calculation validator for line-item tax vs expected statutory rate
- [x] Unit test edge cases (rate transitions, leap years, missing rules)

### Phase 6: Ingestion Pipeline & File Parsers
- [x] Implement CSV stream parser with header autodetection
- [x] Implement Excel (.xlsx) workbook parser via Pandas/openpyxl
- [x] Implement basic PDF structured invoice parser
- [x] Enforce batch hash calculation and deduplication safeguards

### Phase 7: Document Normalization & Sanitization
- [x] Implement alphanumeric invoice number sanitizer
- [x] Build vendor name canonicalization using clean token dictionaries
- [x] Enforce strict ISO-8601 UTC date parsing
- [x] Standardize currency normalization and Decimal conversions

### Phase 8: Core Deterministic Reconciliation Engine
- [x] Implement Pass 1: Exact reference and ID matching
- [x] Implement Pass 2: Exact vendor + exact date + exact amount matching
- [x] Implement Pass 3: Tolerance matching (configurable penny/cent boundaries)
- [x] Persist match records in `reconciliation_results` with confidence scores

### Phase 9: Fuzzy & Semantic Reconciliation Engine
- [x] Integrate `RapidFuzz` for normalized vendor name matching
- [x] Implement Levenshtein distance matching for typo-prone invoice numbers
- [x] Implement semantic embedding matcher for unstructured transaction descriptions
- [x] Calibrate composite confidence scoring thresholds (0.0000 to 1.0000)

### Phase 10: 1:N and N:1 Split Reconciliation
- [x] Build subset-sum search algorithm for one-to-many payments to single invoice
- [x] Build many-to-one batch settlement reconciliation
- [x] Implement greedy heuristic optimization for large split sets
- [x] Write integration tests for complex split billing scenarios

### Phase 11: ML Anomaly Detection (IsolationForest)
- [x] Implement feature extraction pipeline (amount z-score, date lag, tax ratio)
- [x] Train/fit `scikit-learn` `IsolationForest` on baseline transaction profiles
- [x] Combine ML anomaly scores with deterministic statutory red-flags
- [x] Persist flags and feature vectors in `anomalies` table

### Phase 12: Stored Factor Risk Scoring Engine
- [x] Implement factor computation service: Mismatch (25), Exposure (25), Tax (20), Anomaly (15), Vendor (10), Recurrence (5)
- [x] Build classification mapper (LOW <30, MEDIUM 30-54, HIGH 55-74, CRITICAL >=75)
- [x] Store immutable factor breakdown JSON in `cases.factor_breakdown`
- [x] Verify test suite across all risk tiers

### Phase 13: Case Management & State Transition Machine
- [x] Build `CaseService` with strict state machine (`OPEN` -> `IN_REVIEW` -> `RESOLVED` / `REJECTED`)
- [x] Implement automated priority assignment and SLA calculation
- [x] Implement reviewer assignment and escalation workflows
- [x] Write state machine validation tests preventing illegal transitions

### Phase 14: LLM Copilot & Provider Abstraction
- [x] Implement `BaseAIProvider` interface
- [x] Build `GroqProvider` using Groq SDK / REST API
- [x] Build `GeminiProvider` using Google GenAI SDK
- [x] Build `MockAIProvider` operating over live database state
- [x] Build prompt compiler injecting sanitized JSON context with zero DB access

### Phase 15: WhatsApp Channel & Two-Way Confirmation Engine
- [x] Implement Meta WhatsApp Cloud API outbound client
- [x] Build inbound webhook receiver with HMAC signature verification
- [x] Implement state engine for `EXPLAIN`, `REVIEW`, and `CONFIRM <CODE>` commands
- [x] Implement strict guardrail: WhatsApp can only change case status, NEVER ledger records
- [x] Build `simulate-inbound` endpoint for local end-to-end testing

### Phase 16: Canonical Demo Data Generator (Case TX-10482)
- [x] Build database seeder creating tenant, users, vendors, and rules
- [x] Seed Case `TX-10482`: $100k invoice, $100k payment, $97.5k base @ 18% -> $17,550 expected vs $18,000 recorded
- [x] Verify risk score precisely evaluates to `62.00` (`HIGH`)
- [x] Create automated reset endpoint `POST /api/v1/demo/reset`

### Phase 17: FastAPI REST API Implementation
- [x] Implement all 16 endpoint groups adhering to API specification
- [x] Standardize error handlers returning `{ "error": { "code", "message", "details" } }`
- [x] Configure CORS middleware and request ID tracking
- [x] Write integration test suite covering all route handlers

### Phase 18: Frontend Foundation (React + Vite + Tailwind + TanStack Query)
- [x] Initialize React 18 TypeScript application via Vite
- [x] Configure Tailwind CSS with design tokens and status color mappings
- [x] Set up TanStack Query client with caching and retry policies
- [x] Build application shell: Top navigation, sidebar, notifications

### Phase 19: Frontend Reconciliation & Case Management Views
- [x] Build Dashboard view with real-time metrics, risk distribution, and trends
- [x] Build Reconciliation Workbench with side-by-side matching view
- [x] Build Case Detail view showing risk breakdown, factor bars, and AI explanation drawer
- [x] Build WhatsApp Simulator panel for live interactive demonstration

### Phase 20: End-to-End Verification & Production Readiness
- [x] Run automated end-to-end test validating full pipeline (Ingest -> Audit)
- [x] Execute canonical demo verification (`TX-10482`)
- [x] Audit all endpoints for multi-tenant isolation and Decimal precision
- [x] Document final operating procedures and sign off deployment checklist
