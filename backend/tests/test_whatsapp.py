import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from app.services.whatsapp import WhatsAppService, MockWhatsAppProvider
from app.models.models import Organization, Case, User, PendingConfirmation, ReconciliationResult


def test_whatsapp_commands(db):
    org = Organization(name="WA Org", slug="wa-org", tax_identifier="W1")
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id, email="reviewer@wa.com",
        full_name="WA Reviewer", role="REVIEWER", phone_number="+919999999999",
    )
    db.add(user)
    db.flush()

    from app.models.models import ReconciliationRun
    run = ReconciliationRun(organization_id=org.id, status="COMPLETED")
    db.add(run)
    db.flush()

    res = ReconciliationResult(
        organization_id=org.id, run_id=run.id,
        match_type="MANUAL", confidence_score=Decimal("0.9000"),
        variance_amount=Decimal("450.00"), status="TAX_VARIANCE",
    )
    db.add(res)
    db.flush()

    case = Case(
        organization_id=org.id, case_number="TX-10482",
        reconciliation_result_id=res.id, status="OPEN",
        priority="HIGH", risk_score=Decimal("62.00"),
        factor_breakdown={}, financial_exposure=Decimal("100000.00"),
        tax_impact=Decimal("450.00"),
    )
    db.add(case)
    db.flush()

    svc = WhatsAppService()
    phone = "+919999999999"

    # 1. HELP command
    resp = svc.handle_inbound(db, phone, "HELP", org.id)
    assert "TAXPULSE Commands" in resp

    # 2. SUMMARY command
    resp = svc.handle_inbound(db, phone, "SUMMARY", org.id)
    assert "Total cases: 1" in resp

    # 3. CRITICAL command
    resp = svc.handle_inbound(db, phone, "CRITICAL", org.id)
    assert "No critical cases" in resp or "Critical Cases" in resp

    # 4. CASE command
    resp = svc.handle_inbound(db, phone, "CASE TX-10482", org.id)
    assert "Case TX-10482" in resp
    assert "100000.00" in resp

    # 5. REVIEW command -> generates pending confirmation
    resp = svc.handle_inbound(db, phone, "REVIEW TX-10482", org.id)
    assert "CONFIRM TX-10482" in resp
    assert "Valid for 10 minutes" in resp

    # Check pending confirmation exists
    conf = db.query(PendingConfirmation).filter_by(
        organization_id=org.id, confirmation_code="CONFIRM TX-10482", is_used=False
    ).first()
    assert conf is not None

    # 6. CONFIRM command -> updates case to IN_REVIEW
    resp = svc.handle_inbound(db, phone, "CONFIRM TX-10482", org.id)
    assert "marked as IN_REVIEW" in resp
    assert case.status == "IN_REVIEW"
    assert conf.is_used is True

    # 7. CANCEL command
    resp = svc.handle_inbound(db, phone, "CANCEL", org.id)
    assert "cancelled" in resp


def test_whatsapp_alert_format(db):
    org = Organization(name="Alert Org", slug="alert-org", tax_identifier="A1")
    db.add(org)
    db.flush()

    from app.models.models import ReconciliationRun
    run = ReconciliationRun(organization_id=org.id, status="COMPLETED")
    db.add(run)
    db.flush()

    res = ReconciliationResult(
        organization_id=org.id, run_id=run.id, match_type="MANUAL",
        confidence_score=Decimal("0.9"), variance_amount=Decimal("450.00"),
        status="TAX_VARIANCE",
    )
    db.add(res)
    db.flush()

    case = Case(
        organization_id=org.id, case_number="TX-10482",
        reconciliation_result_id=res.id, status="OPEN",
        priority="HIGH", risk_score=Decimal("62.00"),
        factor_breakdown={}, financial_exposure=Decimal("100000.00"),
        tax_impact=Decimal("450.00"),
    )
    db.add(case)
    db.flush()

    svc = WhatsAppService()
    msg = svc.send_alert(db, case, "+919876543210", org.id)
    assert msg.recipient_phone == "+919876543210"
    assert "TX-10482" in msg.message_body
    assert "HIGH" in msg.message_body
    assert "450.00" in msg.message_body
    assert "EXPLAIN TX-10482" in msg.message_body


def test_hmac_signature_validation():
    secret = "my-test-secret"
    payload = b'{"object":"whatsapp_business_account"}'
    signature = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(
        signature,
        "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest(),
    )
