from datetime import date
from decimal import Decimal
import pytest
from app.services.risk import RiskScorer, classify_risk
from app.models.models import (
    Organization, ReconciliationRun, ReconciliationResult,
    Invoice, Vendor, Anomaly,
)


def test_risk_level_boundaries():
    assert classify_risk(0.0) == "LOW"
    assert classify_risk(29.99) == "LOW"
    assert classify_risk(30.0) == "MEDIUM"
    assert classify_risk(54.99) == "MEDIUM"
    assert classify_risk(55.0) == "HIGH"
    assert classify_risk(62.0) == "HIGH"
    assert classify_risk(74.99) == "HIGH"
    assert classify_risk(75.0) == "CRITICAL"
    assert classify_risk(100.0) == "CRITICAL"


def test_risk_scorer_factors(db):
    org = Organization(name="Risk Org", slug="risk-org", tax_identifier="R123")
    db.add(org)
    db.flush()

    run = ReconciliationRun(organization_id=org.id, status="COMPLETED")
    db.add(run)
    db.flush()

    vendor = Vendor(
        organization_id=org.id, name="Test Vendor", normalized_name="test vendor",
        dispute_count=3, risk_tier="HIGH",
    )
    db.add(vendor)
    db.flush()

    invoice = Invoice(
        organization_id=org.id, vendor_id=vendor.id, invoice_number="INV-TEST-1",
        normalized_number="INVTEST1", invoice_date=date(2026, 3, 1),
        subtotal=Decimal("97500.00"), tax_amount=Decimal("18000.00"),
        total_amount=Decimal("100000.00"),
    )
    db.add(invoice)
    db.flush()

    result = ReconciliationResult(
        organization_id=org.id, run_id=run.id, invoice_id=invoice.id,
        match_type="MANUAL", confidence_score=Decimal("0.8500"),
        variance_amount=Decimal("450.00"), status="TAX_VARIANCE",
    )
    db.add(result)
    db.flush()

    anomaly = Anomaly(
        organization_id=org.id, reconciliation_result_id=result.id,
        anomaly_type="TAX_DEVIATION", detector_type="RULE_ENGINE",
        severity_score=Decimal("60.00"), raw_features={},
    )
    db.add(anomaly)
    db.flush()

    scorer = RiskScorer()
    score_data = scorer.score(db, result, anomaly)

    assert score_data["risk_level"] in ("HIGH", "CRITICAL")
    assert score_data["risk_score"] >= Decimal("55.00")
    assert len(score_data["risk_factors"]) == 6
