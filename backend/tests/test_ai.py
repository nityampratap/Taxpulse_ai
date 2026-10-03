import json
from decimal import Decimal
from datetime import date
import pytest
from app.services.ai import (
    AIService, CaseContext, MockAIProvider, _grounding_check,
)
from app.models.models import Organization, Case, Invoice, ReconciliationResult, Vendor


def test_grounding_check():
    context = {
        "invoice": {"subtotal": "97500.00", "tax_amount": "18000.00", "total_amount": "100000.00"},
        "tax_impact": "450.00",
    }
    # Response with numbers in context -> passes
    valid_resp = {
        "summary": "Variance of 450.00 on invoice with subtotal 97500.00 and tax 18000.00",
        "tax_impact": "450.00",
    }
    assert _grounding_check(valid_resp, context) is True

    # Response with hallucinated number -> fails
    hallucinated_resp = {
        "summary": "Variance of 99999.00 on invoice with subtotal 97500.00",
        "tax_impact": "99999.00",
    }
    assert _grounding_check(hallucinated_resp, context) is False


def test_ai_explain_tx10482(db):
    org = Organization(name="AI Org", slug="ai-org", tax_identifier="A1")
    db.add(org)
    db.flush()

    vendor = Vendor(organization_id=org.id, name="ABC Supplies", normalized_name="abc supplies")
    db.add(vendor)
    db.flush()

    inv = Invoice(
        organization_id=org.id, vendor_id=vendor.id, invoice_number="INV-2048",
        normalized_number="INV2048", invoice_date=date(2026, 3, 7),
        subtotal=Decimal("97500.00"), tax_amount=Decimal("18000.00"),
        total_amount=Decimal("100000.00"),
    )
    db.add(inv)
    db.flush()

    from app.models.models import ReconciliationRun
    run = ReconciliationRun(organization_id=org.id, status="COMPLETED")
    db.add(run)
    db.flush()

    result = ReconciliationResult(
        organization_id=org.id, run_id=run.id, invoice_id=inv.id,
        match_type="MANUAL", confidence_score=Decimal("0.9000"),
        variance_amount=Decimal("450.00"), status="TAX_VARIANCE",
        reason_codes=["TAX_DISCREPANCY"],
    )
    db.add(result)
    db.flush()

    case = Case(
        organization_id=org.id, case_number="TX-10482",
        reconciliation_result_id=result.id, status="OPEN",
        priority="HIGH", risk_score=Decimal("62.00"),
        factor_breakdown={}, financial_exposure=Decimal("100000.00"),
        tax_impact=Decimal("450.00"),
    )
    db.add(case)
    db.flush()

    ai_svc = AIService()
    explanation = ai_svc.explain_case(db, case)

    assert explanation["provider"] in ("GROQ", "GEMINI", "MOCK")
    summary = explanation["summary"]
    # Verify key data appears
    assert "97500" in summary
    assert "18000" in summary
    assert "450" in summary
    assert explanation["tax_impact"] == "450.00" or "450" in explanation["tax_impact"]
