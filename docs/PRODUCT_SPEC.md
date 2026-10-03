# TAXPULSE AI — Product Specification

## Executive Summary
| Attribute | Specification |
| :--- | :--- |
| **Product Name** | TAXPULSE AI |
| **Tagline** | Autonomous Tax Reconciliation & Compliance Intelligence |
| **Core Value** | Real-time ingestion, reconciliation, anomaly detection, AI-powered root-cause explanation, and human-in-the-loop dispute resolution across enterprise invoices, ledger entries, and tax returns. |
| **Primary Users** | Tax Controllers, CFOs, Compliance Analysts, AP/AR Accountants |

---

## 1. End-to-End Autonomous Pipeline

| Stage | Name | Input | Processing Engine | Output Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **INGEST** | CSV, Excel (.xlsx), PDF, ERP API | MIME verification, chunked stream reader | Staged raw batches (`import_batches`) |
| **02** | **EXTRACT** | Staged documents | OCR, layout parser, regex field extractor | Key-value pairs & line items |
| **03** | **NORMALIZE** | Extracted fields | ID sanitization, ISO dates, Decimal(18,4), vendor aliases | Canonical entities (`invoices`, `transactions`, `payments`) |
| **04** | **RECONCILE** | Normalized records | Exact, Normalized, Fuzzy, Context-Aware, Semantic, Tolerance, 1:N, N:1 | Reconciled match pairs (`reconciliation_results`) |
| **05** | **DETECT** | Reconciled + Unmatched | IsolationForest ML + Deterministic tax rules | Flagged discrepancies (`anomalies`, `cases`) |
| **06** | **EXPLAIN** | Cases & Anomalies | Structured LLM prompt compiler (Groq / Gemini / Mock) | Root-cause analysis, exposure calculation, citations |
| **07** | **ACT** | Actionable cases | Action dispatcher: Web UI, assignment, WhatsApp bot | Human approval / resolution (`cases`) |
| **08** | **AUDIT** | Every pipeline action | Immutable append-only hash-chained event logger | Regulatory audit trail (`audit_events`) |

---

## 2. Hybrid Intelligence Model

| Engine | Primary Technology | Responsibility & Operational Scope |
| :--- | :--- | :--- |
| **Rule Engine** | Deterministic Python & SQL | Exact invoice number matches, strict date ranges, mathematical tax calculations against active rates. |
| **Fuzzy & Semantic Matcher** | `RapidFuzz` (Levenshtein, token sort, partial ratio) + Embeddings | Normalized vendor variations, invoice typo tolerance, semantic description matching. |
| **ML Anomaly Detection** | `scikit-learn` `IsolationForest` + Statistical Z-scores | Unsupervised outlier detection in amount distributions, payment lag, and tax rate variances. |
| **LLM Copilot** | Pluggable Provider Interface (`Groq`, `Gemini`, `Mock`) | Natural language case explanation, tax regulation reasoning, WhatsApp conversational response formatting. |

---

## 3. Risk Scoring & Classification Model

Risk scores range from `0` to `100`, computed via a stored, explainable factor matrix:

### Factor Weight Distribution
| Factor Name | Max Weight | Evaluation Logic & Triggers |
| :--- | :--- | :--- |
| **Mismatch Severity** | 25 | Unmatched record = 25; Line-item variance = 15; Date/timing mismatch = 5; Perfect match = 0. |
| **Financial Exposure** | 25 | Base exposure: >$100,000 = 25; $50,000–$100,000 = 20; $10,000–$50,000 = 15; <$10,000 = 5. |
| **Tax Impact** | 20 | Absolute statutory tax variance: >$5,000 = 20; $1,000–$5,000 = 15; $100–$1,000 = 10; <$100 = 5. |
| **Anomaly Score** | 15 | IsolationForest anomaly decision function normalized between 0 and 15. |
| **Vendor History** | 10 | Past dispute frequency: High-risk vendor = 10; Moderate = 5; Clean track record = 0. |
| **Recurrence** | 5 | Same mismatch pattern observed across multiple consecutive filing periods = 5. |

### Classification Tiers
| Tier | Score Range | Action Required | Response SLA |
| :--- | :--- | :--- | :--- |
| **LOW** | 0 – 29 | Automated reconciliation or batch sign-off queue | 72 hours |
| **MEDIUM** | 30 – 54 | Assigned to junior compliance analyst review queue | 24 hours |
| **HIGH** | 55 – 74 | Senior accountant review + Automated WhatsApp alert | 8 hours |
| **CRITICAL** | 75 – 100 | Settlement frozen; immediate controller sign-off required | 2 hours |

---

## 4. Key Constraints & Architecture Guarantees

| Constraint | Architectural Rule |
| :--- | :--- |
| **Monetary Precision** | Every monetary value in the database, backend, and calculations MUST use `Decimal` / `NUMERIC(18, 4)`. Floating point math is strictly forbidden. |
| **Multi-Tenancy** | Every single table MUST include an `organization_id` foreign key. Cross-tenant leakage is strictly prevented at the query layer. |
| **Zero DB Access for AI** | The LLM Copilot receives pre-filtered, structured JSON payloads. It has NO direct SQL or database connection. |
| **WhatsApp Guardrails** | WhatsApp interactions can ONLY transition case status (e.g. `PENDING` -> `RESOLVED`) after an explicit two-step `CONFIRM`. WhatsApp NEVER mutates ledger or accounting records. |
| **Temporal Tax Rules** | All statutory tax rates are stored in a dedicated `tax_rules` table with strict `effective_from` and `effective_to` dates. |
| **Real Data Mocking** | Mock AI and WhatsApp providers MUST run against live application state and return contextual data, not hardcoded dummy text. |
| **Database Portability** | Full dual-dialect support: PostgreSQL for production and zero-config SQLite for local development. |
