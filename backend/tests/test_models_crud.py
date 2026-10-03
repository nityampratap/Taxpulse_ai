from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Base,
    Organization,
    User,
    Vendor,
    Invoice,
    Transaction,
    Payment,
    LedgerEntry,
    TaxRule,
    ImportBatch,
    ReconciliationRun,
    ReconciliationResult,
    Anomaly,
    Case,
    CaseAssignment,
    AuditEvent,
    WhatsAppMessage,
    PendingConfirmation,
    AIInteraction,
)
from app.db.seed import seed_database


@pytest.fixture
def db_session():
    # In-memory SQLite for fast isolated testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_seed_database(db_session):
    result = seed_database(db_session)
    assert result["organization"]["slug"] == "taxpulse-org"
    assert len(result["users"]) == 4
    assert result["tax_rules_count"] == 5

    # Verify users exist
    admin = db_session.query(User).filter_by(role="ADMIN").first()
    assert admin is not None
    assert admin.email == "admin@taxpulse.ai"

    # Verify demo tax rule
    rule = db_session.query(TaxRule).filter_by(tax_type="GST", rate=Decimal("0.1800")).first()
    assert rule is not None
    assert rule.is_demo is True


def test_crud_entities(db_session):
    # 1. Organization
    org = Organization(
        name="Acme Corp",
        slug="acme-corp",
        tax_identifier="GSTIN-99999",
    )
    db_session.add(org)
    db_session.commit()

    # 2. User
    user = User(
        organization_id=org.id,
        email="test@acme.com",
        full_name="Test User",
        role="ANALYST",
    )
    db_session.add(user)

    # 3. Vendor
    vendor = Vendor(
        organization_id=org.id,
        name="Apex Logistics Corp",
        normalized_name="apex logistics",
        tax_identifier="GSTIN-APEX1",
        risk_tier="LOW",
    )
    db_session.add(vendor)
    db_session.commit()

    # 4. Invoice with Numeric(18, 2)
    inv = Invoice(
        organization_id=org.id,
        vendor_id=vendor.id,
        invoice_number="INV-2026-001",
        normalized_number="INV2026001",
        invoice_date=date(2026, 3, 1),
        subtotal=Decimal("10000.50"),
        tax_amount=Decimal("1800.09"),
        total_amount=Decimal("11800.59"),
        status="PENDING",
    )
    db_session.add(inv)

    # 5. Transaction with Numeric(18, 2)
    txn = Transaction(
        organization_id=org.id,
        source="BANK_FEED",
        reference_id="TXN-90210",
        transaction_date=date(2026, 3, 2),
        amount=Decimal("11800.59"),
        description="Wire payment to Apex",
    )
    db_session.add(txn)

    # 6. Payment with Numeric(18, 2)
    pmt = Payment(
        organization_id=org.id,
        invoice_id=inv.id,
        payment_reference="PAY-888",
        payment_date=date(2026, 3, 3),
        amount_paid=Decimal("11800.59"),
        payment_method="WIRE",
        status="COMPLETED",
    )
    db_session.add(pmt)

    # 7. LedgerEntry
    ledger = LedgerEntry(
        organization_id=org.id,
        account_code="2000-AP",
        entry_date=date(2026, 3, 3),
        debit=Decimal("11800.59"),
        credit=Decimal("0.00"),
    )
    db_session.add(ledger)

    # 8. ImportBatch & ReconciliationRun
    batch = ImportBatch(
        organization_id=org.id,
        source_type="CSV",
        file_name="bank_statement.csv",
        file_hash="hash123456",
        row_count=1,
    )
    db_session.add(batch)
    db_session.commit()

    run = ReconciliationRun(
        organization_id=org.id,
        batch_id=batch.id,
        status="COMPLETED",
        total_processed=1,
        matched_count=1,
    )
    db_session.add(run)
    db_session.commit()

    # 9. ReconciliationResult
    res = ReconciliationResult(
        organization_id=org.id,
        run_id=run.id,
        invoice_id=inv.id,
        transaction_id=txn.id,
        payment_id=pmt.id,
        match_type="EXACT",
        confidence_score=Decimal("1.0000"),
        variance_amount=Decimal("0.00"),
        status="MATCHED",
    )
    db_session.add(res)
    db_session.commit()

    # 10. Case & Anomaly
    case = Case(
        organization_id=org.id,
        case_number="CASE-001",
        reconciliation_result_id=res.id,
        status="OPEN",
        priority="HIGH",
        risk_score=Decimal("62.00"),
        factor_breakdown={"mismatch": 15, "exposure": 15, "tax": 10},
        financial_exposure=Decimal("11800.59"),
        tax_impact=Decimal("0.00"),
    )
    db_session.add(case)
    db_session.commit()

    # 11. AuditEvent
    audit = AuditEvent(
        organization_id=org.id,
        event_type="CASE_CREATED",
        actor_id=user.id,
        entity_type="case",
        entity_id=case.id,
        after_state={"status": "OPEN"},
        hash_checksum="checksum-abc",
    )
    db_session.add(audit)

    # 12. WhatsAppMessage & PendingConfirmation
    wa = WhatsAppMessage(
        organization_id=org.id,
        case_id=case.id,
        recipient_phone="+1234567890",
        direction="OUTBOUND",
        message_body="Case Alert",
        status="SENT",
    )
    db_session.add(wa)

    conf = PendingConfirmation(
        organization_id=org.id,
        case_id=case.id,
        confirmation_code="CONFIRM 1234",
        action_payload={"target_status": "RESOLVED"},
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(conf)

    # 13. AIInteraction
    ai = AIInteraction(
        organization_id=org.id,
        case_id=case.id,
        provider="MOCK",
        prompt_context={"case_number": "CASE-001"},
        response_text="Analysis complete",
    )
    db_session.add(ai)
    db_session.commit()

    # Query verification
    retrieved_case = db_session.query(Case).filter_by(case_number="CASE-001").first()
    assert retrieved_case is not None
    assert retrieved_case.financial_exposure == Decimal("11800.59")
    assert retrieved_case.factor_breakdown["mismatch"] == 15
    assert retrieved_case.risk_score == Decimal("62.00")
