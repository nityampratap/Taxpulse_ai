# TAXPULSE AI — Data Model Specification

All tables enforce multi-tenancy via `organization_id`. All currency and monetary amounts MUST use `NUMERIC(18, 4)` / `Decimal`.

---

## Entity Relationship Overview

| Table | Purpose | Primary Key | Key Foreign Keys |
| :--- | :--- | :--- | :--- |
| `organizations` | Tenant accounts | `id` | None |
| `users` | User credentials & roles | `id` | `organization_id` |
| `vendors` | Vendor directory & risk history | `id` | `organization_id` |
| `invoices` | Invoices received or issued | `id` | `organization_id`, `vendor_id` |
| `transactions` | Bank & ledger transaction feeds | `id` | `organization_id` |
| `payments` | Disbursed or received payments | `id` | `organization_id`, `invoice_id` |
| `ledger_entries` | General ledger line items | `id` | `organization_id` |
| `tax_rules` | Jurisdictional rates with effective dates | `id` | `organization_id` |
| `import_batches` | File ingestion jobs & status | `id` | `organization_id` |
| `reconciliation_runs` | Execution runs of matching engine | `id` | `organization_id`, `batch_id` |
| `reconciliation_results` | Individual match links & variances | `id` | `organization_id`, `run_id`, `invoice_id`, `transaction_id`, `payment_id` |
| `anomalies` | Detected anomalies & ML flags | `id` | `organization_id`, `reconciliation_result_id` |
| `cases` | Actionable discrepancy tickets | `id` | `organization_id`, `reconciliation_result_id` |
| `case_assignments` | Workflow reviewer assignments | `id` | `organization_id`, `case_id`, `assigned_to_user_id` |
| `audit_events` | Immutable compliance audit stream | `id` | `organization_id`, `actor_id` |
| `whatsapp_messages` | Inbound/outbound message log | `id` | `organization_id`, `case_id` |
| `pending_confirmations` | Temporary two-factor action tokens | `id` | `organization_id`, `case_id` |
| `ai_interactions` | LLM prompt/response audit records | `id` | `organization_id`, `case_id` |

---

## Detailed Schema Definitions

### 1. `organizations`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique organization ID (UUID) |
| `name` | VARCHAR(255) | NOT NULL | Legal corporate entity name |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly unique identifier |
| `tax_identifier` | VARCHAR(50) | NOT NULL | GSTIN / EIN / VAT identifier |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Registration timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

### 2. `users`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique user ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `email` | VARCHAR(255) | NOT NULL | User email address |
| `full_name` | VARCHAR(255) | NOT NULL | Full name of user |
| `role` | VARCHAR(50) | NOT NULL | `ADMIN`, `ANALYST`, `REVIEWER`, `AUDITOR` |
| `phone_number` | VARCHAR(30) | NULL | E.164 phone number for WhatsApp alerts |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active flag |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |

### 3. `vendors`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique vendor ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `name` | VARCHAR(255) | NOT NULL | Registered vendor trade name |
| `normalized_name` | VARCHAR(255) | NOT NULL | Cleaned/standardized vendor name for fuzzy matching |
| `tax_identifier` | VARCHAR(50) | NULL | Vendor GSTIN / Tax ID |
| `risk_tier` | VARCHAR(20) | NOT NULL, DEFAULT 'LOW' | `LOW`, `MEDIUM`, `HIGH` |
| `dispute_count` | INTEGER | NOT NULL, DEFAULT 0 | Historical reconciliation disputes count |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Registration timestamp |

### 4. `invoices`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique invoice ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `vendor_id` | VARCHAR(36) | NOT NULL, FK(`vendors.id`) | Associated vendor ID |
| `invoice_number` | VARCHAR(100) | NOT NULL | Raw invoice number |
| `normalized_number` | VARCHAR(100) | NOT NULL | Stripped alphanumeric reference |
| `invoice_date` | DATE | NOT NULL | Issued date |
| `due_date` | DATE | NULL | Payment due date |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'USD' | ISO-4217 currency code |
| `subtotal` | NUMERIC(18, 4) | NOT NULL | Taxable base amount |
| `tax_amount` | NUMERIC(18, 4) | NOT NULL | Total recorded tax |
| `total_amount` | NUMERIC(18, 4) | NOT NULL | Gross invoice amount |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'PENDING' | `PENDING`, `RECONCILED`, `DISPUTED` |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation timestamp |

### 5. `transactions`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique transaction ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `source` | VARCHAR(50) | NOT NULL | `BANK_FEED`, `ERP_GL`, `CREDIT_CARD` |
| `reference_id` | VARCHAR(100) | NOT NULL | Bank/external reference ID |
| `transaction_date` | DATE | NOT NULL | Value date |
| `amount` | NUMERIC(18, 4) | NOT NULL | Transaction value |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'USD' | Currency code |
| `description` | TEXT | NULL | Raw transaction memo/description |
| `counterparty_name` | VARCHAR(255) | NULL | Raw counterparty string |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation timestamp |

### 6. `payments`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique payment ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `invoice_id` | VARCHAR(36) | NULL, FK(`invoices.id`) | Associated invoice ID if matched |
| `payment_reference` | VARCHAR(100) | NOT NULL | Payment reference / UTR / Check # |
| `payment_date` | DATE | NOT NULL | Date payment cleared |
| `amount_paid` | NUMERIC(18, 4) | NOT NULL | Total disbursed amount |
| `payment_method` | VARCHAR(50) | NOT NULL | `ACH`, `WIRE`, `CHECK`, `CARD` |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'COMPLETED' | `PENDING`, `COMPLETED`, `REVERSED` |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation timestamp |

### 7. `ledger_entries`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique ledger entry ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `account_code` | VARCHAR(50) | NOT NULL | Chart of accounts code |
| `entry_date` | DATE | NOT NULL | Accounting posting date |
| `debit` | NUMERIC(18, 4) | NOT NULL, DEFAULT 0 | Debit amount |
| `credit` | NUMERIC(18, 4) | NOT NULL, DEFAULT 0 | Credit amount |
| `description` | TEXT | NULL | Journal memo |
| `reference_id` | VARCHAR(100) | NULL | Document reference |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation timestamp |

### 8. `tax_rules`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique tax rule ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `tax_type` | VARCHAR(50) | NOT NULL | `GST`, `VAT`, `SALES_TAX`, `WITHHOLDING` |
| `jurisdiction` | VARCHAR(100) | NOT NULL | Country/State code (e.g., 'IN-MH', 'US-CA') |
| `rate` | NUMERIC(6, 4) | NOT NULL | Statutory rate percentage (e.g., 0.1800 for 18%) |
| `effective_from` | DATE | NOT NULL | Start date of rate applicability |
| `effective_to` | DATE | NULL | End date of rate applicability (NULL = active) |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Status flag |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |

### 9. `import_batches`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique import batch ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `source_type` | VARCHAR(50) | NOT NULL | `CSV`, `EXCEL`, `PDF`, `API` |
| `file_name` | VARCHAR(255) | NOT NULL | Uploaded filename |
| `file_hash` | VARCHAR(64) | NOT NULL | SHA-256 integrity hash |
| `row_count` | INTEGER | NOT NULL, DEFAULT 0 | Number of ingested lines |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'PENDING' | `PENDING`, `PARSED`, `FAILED` |
| `ingested_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Ingestion timestamp |

### 10. `reconciliation_runs`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique reconciliation run ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `batch_id` | VARCHAR(36) | NULL, FK(`import_batches.id`) | Batch trigger |
| `run_timestamp` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Execution start |
| `status` | VARCHAR(50) | NOT NULL | `IN_PROGRESS`, `COMPLETED`, `FAILED` |
| `total_processed` | INTEGER | NOT NULL, DEFAULT 0 | Total records evaluated |
| `matched_count` | INTEGER | NOT NULL, DEFAULT 0 | Successfully matched count |
| `variance_count` | INTEGER | NOT NULL, DEFAULT 0 | Records with discrepancy |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |

### 11. `reconciliation_results`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique result ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `run_id` | VARCHAR(36) | NOT NULL, FK(`reconciliation_runs.id`) | Parent run ID |
| `invoice_id` | VARCHAR(36) | NULL, FK(`invoices.id`) | Linked invoice |
| `transaction_id` | VARCHAR(36) | NULL, FK(`transactions.id`) | Linked transaction |
| `payment_id` | VARCHAR(36) | NULL, FK(`payments.id`) | Linked payment |
| `match_type` | VARCHAR(50) | NOT NULL | `EXACT`, `FUZZY`, `SEMANTIC`, `SPLIT_1_N`, `SPLIT_N_1`, `MANUAL` |
| `confidence_score` | NUMERIC(5, 4) | NOT NULL | Match confidence (0.0000 to 1.0000) |
| `variance_amount` | NUMERIC(18, 4) | NOT NULL, DEFAULT 0 | Net monetary discrepancy |
| `status` | VARCHAR(50) | NOT NULL | `MATCHED`, `VARIANCE`, `UNMATCHED` |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |

### 12. `anomalies`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique anomaly ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `reconciliation_result_id` | VARCHAR(36) | NOT NULL, FK(`reconciliation_results.id`) | Result reference |
| `anomaly_type` | VARCHAR(50) | NOT NULL | `TAX_RATE_VARIANCE`, `DUPLICATE_PAYMENT`, `MISSING_RECORD`, `STATISTICAL_OUTLIER` |
| `detector_type` | VARCHAR(50) | NOT NULL | `ISOLATION_FOREST`, `RULE_ENGINE`, `Z_SCORE` |
| `severity_score` | NUMERIC(5, 2) | NOT NULL | Detected anomaly severity (0–100) |
| `raw_features` | JSON | NOT NULL | Feature vector or diagnostic JSON payload |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Detection timestamp |

### 13. `cases`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique case ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `case_number` | VARCHAR(50) | UNIQUE, NOT NULL | Human-readable case code (e.g. 'TX-10482') |
| `reconciliation_result_id` | VARCHAR(36) | NOT NULL, FK(`reconciliation_results.id`) | Discrepancy origin |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'OPEN' | `OPEN`, `IN_REVIEW`, `ESCALATED`, `RESOLVED`, `REJECTED` |
| `priority` | VARCHAR(20) | NOT NULL | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `risk_score` | NUMERIC(5, 2) | NOT NULL | Stored composite risk score (0–100) |
| `factor_breakdown` | JSON | NOT NULL | Stored factor contributions dictionary |
| `financial_exposure` | NUMERIC(18, 4) | NOT NULL | Gross financial amount in dispute |
| `tax_impact` | NUMERIC(18, 4) | NOT NULL | Disputed statutory tax variance |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

### 14. `case_assignments`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique assignment ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `case_id` | VARCHAR(36) | NOT NULL, FK(`cases.id`) | Assigned case |
| `assigned_to_user_id` | VARCHAR(36) | NOT NULL, FK(`users.id`) | Assignee |
| `assigned_by_user_id` | VARCHAR(36) | NOT NULL, FK(`users.id`) | Assignor |
| `assigned_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp of assignment |
| `sla_due_at` | TIMESTAMP | NOT NULL | SLA deadline |

### 15. `audit_events`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique audit event ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `event_type` | VARCHAR(100) | NOT NULL | E.g. `CASE_STATUS_CHANGED`, `RECON_EXECUTED`, `AI_EXPLAIN_REQUESTED` |
| `actor_id` | VARCHAR(36) | NOT NULL | User ID, 'SYSTEM', or 'WHATSAPP_BOT' |
| `entity_type` | VARCHAR(50) | NOT NULL | `case`, `reconciliation_result`, `tax_rule` |
| `entity_id` | VARCHAR(36) | NOT NULL | Target entity ID |
| `before_state` | JSON | NULL | JSON snapshot prior to mutation |
| `after_state` | JSON | NOT NULL | JSON snapshot following mutation |
| `hash_checksum` | VARCHAR(64) | NOT NULL | SHA-256 tamper-evident integrity hash |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Immutable audit event timestamp |

### 16. `whatsapp_messages`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique message ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `case_id` | VARCHAR(36) | NULL, FK(`cases.id`) | Associated case if applicable |
| `recipient_phone` | VARCHAR(30) | NOT NULL | Destination E.164 phone number |
| `direction` | VARCHAR(10) | NOT NULL | `OUTBOUND`, `INBOUND` |
| `message_body` | TEXT | NOT NULL | Message text payload |
| `status` | VARCHAR(30) | NOT NULL | `SENT`, `DELIVERED`, `READ`, `FAILED`, `RECEIVED` |
| `sent_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Dispatch or receipt timestamp |

### 17. `pending_confirmations`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique confirmation token ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `case_id` | VARCHAR(36) | NOT NULL, FK(`cases.id`) | Target case |
| `confirmation_code` | VARCHAR(20) | UNIQUE, NOT NULL | Alphanumeric token (e.g., 'CONFIRM 8472') |
| `action_payload` | JSON | NOT NULL | Target state transition metadata |
| `expires_at` | TIMESTAMP | NOT NULL | Expiration timestamp (15-min TTL) |
| `is_used` | BOOLEAN | NOT NULL, DEFAULT FALSE | Idempotency guard flag |
| `confirmed_at` | TIMESTAMP | NULL | Confirmation timestamp |

### 18. `ai_interactions`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique interaction ID (UUID) |
| `organization_id` | VARCHAR(36) | NOT NULL, FK(`organizations.id`) | Tenant ID |
| `case_id` | VARCHAR(36) | NULL, FK(`cases.id`) | Associated case |
| `provider` | VARCHAR(50) | NOT NULL | `GROQ`, `GEMINI`, `MOCK` |
| `prompt_context` | JSON | NOT NULL | Structured prompt payload supplied to LLM |
| `response_text` | TEXT | NOT NULL | Structured explanation / advice output |
| `tokens_used` | INTEGER | NOT NULL, DEFAULT 0 | LLM token count consumed |
| `latency_ms` | INTEGER | NOT NULL, DEFAULT 0 | Generation response time |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp of LLM query |
