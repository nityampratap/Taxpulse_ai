# TAXPULSE AI — Architecture Decision Records (ADRs)

| ADR ID | Title | Status | Date |
| :--- | :--- | :--- | :--- |
| **ADR-001** | Dual Database Dialect Architecture (PostgreSQL + SQLite) | **Accepted** | 2026-10-03 |
| **ADR-002** | Mandatory Decimal Arithmetic for Financial & Tax Values | **Accepted** | 2026-10-03 |
| **ADR-003** | Universal Multi-Tenancy Partitioning via `organization_id` | **Accepted** | 2026-10-03 |
| **ADR-004** | AI Copilot Context Isolation & Zero Database Execution Access | **Accepted** | 2026-10-03 |
| **ADR-005** | WhatsApp State Machine & Accounting Immutability Guardrail | **Accepted** | 2026-10-03 |
| **ADR-006** | Hybrid Multi-Layer Reconciliation Hierarchy | **Accepted** | 2026-10-03 |
| **ADR-007** | Stored Factor Decomposition for Audit-Grade Risk Scoring | **Accepted** | 2026-10-03 |
| **ADR-008** | Temporal Tax Rules with Effective Date Boundaries | **Accepted** | 2026-10-03 |

---

## ADR-001: Dual Database Dialect Architecture
- **Context**: Production requires PostgreSQL for concurrent ACID transactions and scaling, while local developers and quick test environments require a zero-setup SQLite fallback.
- **Decision**: Use SQLAlchemy ORM with engine URL auto-detection. When `DATABASE_URL` starts with `sqlite`, enable foreign key enforcement pragmas (`PRAGMA foreign_keys=ON`).
- **Consequences**: Developers can clone and run tests without hosting a local Docker/PostgreSQL instance, while production deploys cleanly to Neon or Supabase PostgreSQL.

---

## ADR-002: Mandatory Decimal Arithmetic
- **Context**: IEEE-754 floating point arithmetic introduces rounding errors (e.g. `0.1 + 0.2 = 0.30000000000000004`), which is unacceptable in regulatory tax calculations.
- **Decision**: All financial amounts in Python must use `decimal.Decimal` and all database columns must use `NUMERIC(18, 4)`. Floating point casts are prohibited in business logic.
- **Consequences**: Guarantees zero precision loss across all reconciliation calculations and currency math.

---

## ADR-003: Universal Multi-Tenancy Partitioning
- **Context**: Compliance data across different enterprises must remain strictly isolated.
- **Decision**: Every database table includes an `organization_id` foreign key. All repository accessors require `organization_id` filters extracted from verified JWT credentials.
- **Consequences**: Cross-tenant data leakage is structurally prevented at both the database schema and application layer.

---

## ADR-004: AI Copilot Context Isolation
- **Context**: Direct SQL execution or database access by LLMs poses prompt injection, unintended mutation, and latency risks.
- **Decision**: The LLM Copilot is strictly fed pre-compiled, sanitized JSON context documents. It has no DB connection, tools, or SQL query privileges.
- **Consequences**: Completely eliminates SQL injection via LLM and guarantees predictable token consumption and latency.

---

## ADR-005: WhatsApp State Machine Guardrails
- **Context**: Discrepancy alerts dispatched via WhatsApp require quick mobile resolution, but remote messaging channels are susceptible to accidental taps or unauthorized spoofing.
- **Decision**: WhatsApp commands can only transition case status (`OPEN` -> `RESOLVED`) after an explicit two-step confirmation token (`CONFIRM <CODE>`). WhatsApp can NEVER modify accounting ledger entries or financial records.
- **Consequences**: Protects general ledger integrity while providing seamless mobile resolution workflows for controllers.

---

## ADR-006: Hybrid Multi-Layer Reconciliation Hierarchy
- **Context**: Real-world financial feeds exhibit varying degrees of dirty data—from perfect exact matches to messy OCR invoice numbers and vendor typos.
- **Decision**: Implement a prioritized pipeline: (1) Deterministic exact matching, (2) Normalized ID matching, (3) RapidFuzz string distance, (4) Semantic embeddings, (5) Split-sum 1:N / N:1 resolution.
- **Consequences**: High-confidence matches are processed in microseconds, reserving computationally expensive fuzzy and ML models for genuine edge cases.

---

## ADR-007: Stored Factor Decomposition for Risk Scoring
- **Context**: Audited financial systems require explainable risk scores rather than opaque 'black box' numbers.
- **Decision**: Composite risk scores (0–100) are computed from 6 discrete factors and stored as a structured JSON factor dictionary alongside the score in `cases.factor_breakdown`.
- **Consequences**: External auditors can inspect exactly why a case was flagged as CRITICAL or HIGH at any point in the future.

---

## ADR-008: Temporal Tax Rules with Effective Date Boundaries
- **Context**: Statutory tax rates change over time (e.g. GST rate revisions or temporary tax holidays).
- **Decision**: `tax_rules` requires `effective_from` and `effective_to` date boundaries. The tax engine queries rules based on the transaction or invoice issue date.
- **Consequences**: Prevents retroactive calculation errors when reconciling historical invoices under prior tax regimes.
