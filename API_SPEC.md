# TAXPULSE AI — REST API Specification

## Standard Error Format
All endpoints return standard HTTP error responses adhering to this schema:

```json
{
  "error": {
    "code": "TAX_RULE_NOT_FOUND",
    "message": "No active tax rule found for jurisdiction IN-MH on date 2026-03-15",
    "details": {
      "jurisdiction": "IN-MH",
      "date": "2026-03-15"
    }
  }
}
```

---

## Endpoint Groups

| Group | Method | Path | Description | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| **health** | `GET` | `/api/v1/health` | Service liveness probe | `200 OK` |
| | `GET` | `/api/v1/health/db` | Database connection & latency probe | `200 OK` |
| **auth** | `POST` | `/api/v1/auth/token` | User authentication & JWT issuance | `200 OK` |
| | `GET` | `/api/v1/auth/me` | Fetch authenticated identity & role | `200 OK` |
| **imports** | `POST` | `/api/v1/imports/upload` | Multipart file upload (CSV, XLSX, PDF) | `201 Created` |
| | `GET` | `/api/v1/imports/batches` | List ingestion batches with statuses | `200 OK` |
| | `GET` | `/api/v1/imports/{batch_id}` | Retrieve batch details and parsed line count | `200 OK` |
| **demo** | `POST` | `/api/v1/demo/generate` | Seed deterministic demo dataset (including `TX-10482`) | `201 Created` |
| | `POST` | `/api/v1/demo/reset` | Purge demo dataset back to pristine state | `200 OK` |
| **transactions**| `GET` | `/api/v1/transactions` | Paginated filterable transaction list | `200 OK` |
| | `GET` | `/api/v1/transactions/{id}` | Retrieve individual transaction record | `200 OK` |
| | `POST` | `/api/v1/transactions` | Create manual transaction entry | `201 Created` |
| **reconciliation**| `POST` | `/api/v1/reconciliation/run` | Trigger multi-pass reconciliation engine | `202 Accepted` |
| | `GET` | `/api/v1/reconciliation/runs` | List execution history and statistics | `200 OK` |
| | `GET` | `/api/v1/reconciliation/results/{id}` | Inspect matched entity graph and confidence | `200 OK` |
| **exceptions** | `GET` | `/api/v1/exceptions` | Filter unmatched records and variances | `200 OK` |
| | `GET` | `/api/v1/exceptions/{id}` | Inspect exception details and candidate matches | `200 OK` |
| **cases** | `GET` | `/api/v1/cases` | List compliance cases filtered by risk tier/status | `200 OK` |
| | `GET` | `/api/v1/cases/{id}` | Full case payload (factors, records, AI logs) | `200 OK` |
| | `POST` | `/api/v1/cases/{id}/review` | Transition case to `IN_REVIEW` | `200 OK` |
| | `POST` | `/api/v1/cases/{id}/assign` | Assign reviewer and calculate SLA deadline | `200 OK` |
| | `POST` | `/api/v1/cases/{id}/escalate` | Elevate priority to `CRITICAL` & alert controller | `200 OK` |
| | `POST` | `/api/v1/cases/{id}/resolve` | Resolve case with audit resolution rationale | `200 OK` |
| | `POST` | `/api/v1/cases/{id}/request-correction` | Generate correction request ticket for vendor | `200 OK` |
| **tax** | `GET` | `/api/v1/tax/rules` | Fetch jurisdictional statutory tax rates | `200 OK` |
| | `POST` | `/api/v1/tax/rules` | Register or update temporal tax rule | `201 Created` |
| | `POST` | `/api/v1/tax/calculate` | Test statutory tax calculation for amount & date | `200 OK` |
| **vendors** | `GET` | `/api/v1/vendors` | List vendors with aggregate risk tiers | `200 OK` |
| | `GET` | `/api/v1/vendors/{id}` | Fetch vendor details & tax ID | `200 OK` |
| | `GET` | `/api/v1/vendors/{id}/history` | Historical dispute and reconciliation records | `200 OK` |
| **dashboard** | `GET` | `/api/v1/dashboard/metrics` | Real-time exposure, match rate, open cases | `200 OK` |
| | `GET` | `/api/v1/dashboard/trends` | 30-day reconciliation volume & variance trend | `200 OK` |
| | `GET` | `/api/v1/dashboard/risk-distribution` | Breakdown of cases across LOW/MED/HIGH/CRIT | `200 OK` |
| **reports** | `GET` | `/api/v1/reports/reconciliation`| Comprehensive period reconciliation statement | `200 OK` |
| | `GET` | `/api/v1/reports/tax-liability` | Statutory tax liability vs recorded variance report | `200 OK` |
| | `POST` | `/api/v1/reports/export` | Stream CSV or Excel export of report | `200 OK` |
| **ai** | `POST` | `/api/v1/ai/explain-case` | Generate LLM root cause & regulatory explanation | `200 OK` |
| | `POST` | `/api/v1/ai/summary` | Generate executive batch reconciliation summary | `200 OK` |
| | `POST` | `/api/v1/ai/ask` | Ask conversational tax copilot question | `200 OK` |
| **whatsapp** | `GET` | `/api/v1/whatsapp/status` | Health & webhook connectivity status | `200 OK` |
| | `POST` | `/api/v1/whatsapp/send` | Dispatch outbound notification to reviewer | `200 OK` |
| | `GET` | `/api/v1/whatsapp/webhook` | Meta Cloud API webhook verification challenge | `200 OK` |
| | `POST` | `/api/v1/whatsapp/webhook` | Inbound message webhook receiver | `200 OK` |
| | `GET` | `/api/v1/whatsapp/conversations`| Message history log for cases | `200 OK` |
| | `POST` | `/api/v1/whatsapp/simulate-inbound` | Testing endpoint to simulate reviewer messages | `200 OK` |
| **audit** | `GET` | `/api/v1/audit/events` | Paginated immutable audit trail stream | `200 OK` |
| | `GET` | `/api/v1/audit/events/{id}` | Inspect specific audit event and SHA-256 hash | `200 OK` |
| **settings** | `GET` | `/api/v1/settings` | Retrieve organization settings & thresholds | `200 OK` |
| | `PUT` | `/api/v1/settings` | Update matching tolerances & SLA parameters | `200 OK` |
