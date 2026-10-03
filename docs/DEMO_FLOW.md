# TAXPULSE AI — Canonical Demo Flow (Case TX-10482)

## Demo Scenario Overview

The flagship demonstration showcases the automated detection, risk scoring, AI explanation, WhatsApp alerting, and state-guarded resolution of a statutory tax variance.

| Step | Action | Endpoint / Interface | Output / Verification |
| :--- | :--- | :--- | :--- |
| **1** | **Generate Demo Data** | `POST /api/v1/demo/generate` | Ingests vendor "Apex Global Logistics", Invoice #INV-2026-904, Bank Transaction #TX-10482, and associated payments. |
| **2** | **Run Reconciliation** | `POST /api/v1/reconciliation/run` | Matching engine pairs records, detects tax variance, and instantiates Case `TX-10482`. |
| **3** | **Open Case TX-10482** | `GET /api/v1/cases/TX-10482` | Displays financial exposure, variance breakdown, and risk scoring factors. |
| **4** | **Inspect Risk Breakdown** | Web UI / API Response | Confirms composite score of `62.00` (`HIGH` priority). |
| **5** | **Invoke AI Explain** | `POST /api/v1/ai/explain-case` | LLM returns root cause, statutory tax law citation, and remediation options. |
| **6** | **Dispatch WhatsApp Alert** | `POST /api/v1/whatsapp/send` | WhatsApp notification dispatched to reviewer with action prompt. |
| **7** | **Interactive Review** | Reviewer replies `EXPLAIN` | Bot replies with itemized tax discrepancy summary. |
| **8** | **Request Confirmation** | Reviewer replies `REVIEW` | Bot returns pending confirmation code `CONFIRM 8472` with 15-min expiration. |
| **9** | **Execute Confirmation** | Reviewer replies `CONFIRM 8472`| Case transitions safely to `RESOLVED`. Accounting records remain unmutated. |
| **10**| **Verify Dashboard & Audit**| `GET /api/v1/dashboard/metrics` & `GET /api/v1/audit/events` | Metrics update in real-time; immutable audit record with cryptographic hash generated. |

---

## Canonical Numbers for Case TX-10482

| Financial Attribute | Value (USD) | Formula / Rule |
| :--- | :--- | :--- |
| **Gross Invoice Total** | $100,000.00 | Total billed by vendor Apex Global Logistics |
| **Gross Payment Cleared**| $100,000.00 | Total cleared via corporate bank account |
| **Taxable Base Amount** | $97,500.00 | Line-item subtotal eligible for statutory tax |
| **Statutory Tax Rule** | 18.00% (0.1800) | Active rate in `tax_rules` for jurisdiction |
| **Expected Statutory Tax**| **$17,550.00** | `$97,500.00 * 0.1800` |
| **Recorded Invoice Tax** | **$18,000.00** | Tax erroneously entered by vendor |
| **Net Tax Variance** | **$450.00** | `$18,000.00 - $17,550.00` (Statutory Overpayment) |

---

## Stored Risk Factor Score Breakdown (Score: 62 / HIGH)

| Factor | Weight Contributed | Max Possible | Scoring Rationale |
| :--- | :--- | :--- | :--- |
| **Mismatch Severity** | 15.00 | 25.00 | Subtotal matches payment, but line-item statutory tax calculation fails verification. |
| **Financial Exposure** | 15.00 | 25.00 | Gross transaction value is $100,000.00 (Tier: $50k–$100k exposure). |
| **Tax Impact** | 10.00 | 20.00 | Net statutory tax variance is $450.00 (Tier: $100–$1,000 variance). |
| **Anomaly Score** | 12.00 | 15.00 | IsolationForest flagged statistical outlier on tax-to-subtotal ratio for this vendor. |
| **Vendor History** | 5.00 | 10.00 | Vendor Apex Global has had 2 prior discrepancies in the preceding 6 months. |
| **Recurrence** | 5.00 | 5.00 | Identical $450 rate mismatch occurred in the prior monthly filing period. |
| **TOTAL SCORE** | **62.00** | **100.00** | **Classification Tier: HIGH (Range: 55–74)** |

---

## Conversational WhatsApp Interaction Script

```text
[SYSTEM -> REVIEWER]
⚠️ TAXPULSE ALERT: High-risk tax variance detected on Case TX-10482.
Vendor: Apex Global Logistics
Exposure: $100,000.00 | Tax Variance: $450.00 (18% Statutory)
Reply EXPLAIN for analysis, or REVIEW to process.

[REVIEWER -> SYSTEM]
EXPLAIN

[SYSTEM -> REVIEWER]
📋 TAXPULSE AI ANALYSIS (Case TX-10482):
• Taxable base: $97,500.00 @ 18% statutory tax = $17,550.00.
• Recorded tax: $18,000.00.
• Discrepancy: $450.00 over-collected tax.
• Statutory Reference: Section 16(2) compliance violation.
• Recommendation: Issue credit note request to vendor or accept adjusted liability.
Reply REVIEW to proceed to sign-off.

[REVIEWER -> SYSTEM]
REVIEW

[SYSTEM -> REVIEWER]
🔒 PENDING CONFIRMATION:
You are about to resolve Case TX-10482 with credit note request adjustment.
Security Token: 8472 (Valid for 15 minutes).
To approve, reply:
CONFIRM 8472

[REVIEWER -> SYSTEM]
CONFIRM 8472

[SYSTEM -> REVIEWER]
✅ Case TX-10482 marked as RESOLVED.
Audit hash: a8f9e12...b9
Dashboard metrics and compliance ledger updated.
```
