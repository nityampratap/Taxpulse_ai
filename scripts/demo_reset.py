"""
TaxPulse AI - Canonical Demo Reset Script (Cross-Platform)
Clears DB, applies schema, seeds 105 demo rows, executes reconciliation and case creation,
verifies pinned case TX-10482, and confirms demo readiness.
"""
import sys
from decimal import Decimal
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal, engine, Base
from app.models.models import Organization, Case, Invoice, ReconciliationResult
from scripts.generate_demo_data import seed_demo_data_to_db
from app.services.reconciliation.engine import ReconciliationEngine
from app.services.anomaly import AnomalyDetector
from app.services.cases import CaseService


def reset_demo():
    print("=" * 60)
    print(" TAXPULSE AI - CANONICAL DEMO ENVIRONMENT RESET")
    print("=" * 60)

    # 1. Reset tables
    print("[1/5] Recreating database tables...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()

    # 2. Seed 105 invoices & relationships
    print("[2/5] Seeding deterministic demo dataset (105 invoices, 4 roles)...")
    meta = seed_demo_data_to_db(db)
    db.commit()
    print(f"      Seeded {meta['total_invoices']} invoices across 8 vendors.")

    # 3. Execute reconciliation engine
    print("[3/5] Running reconciliation passes (exact, fuzzy, context, split)...")
    org = db.query(Organization).first()
    engine_svc = ReconciliationEngine()
    run = engine_svc.run(db, org.id)
    db.commit()
    print(f"      Processed {run.total_processed} items ({run.matched_count} matched, {run.variance_count} variances).")

    # 4. Detect anomalies and create cases
    print("[4/5] Running anomaly detection and risk scoring...")
    results = db.query(ReconciliationResult).filter_by(run_id=run.id).all()
    AnomalyDetector().detect(db, org.id, results)
    cases = CaseService().create_cases_from_results(db, org.id, results)
    db.commit()
    print(f"      Created {len(cases)} exception investigation cases.")

    # 5. Verify canonical pinned case TX-10482
    print("[5/5] Verifying canonical demo case TX-10482...")
    case = db.query(Case).filter_by(case_number="TX-10482").first()
    if not case:
        print("ERROR: Case TX-10482 not found!")
        sys.exit(1)

    inv = db.query(Invoice).filter_by(invoice_number="INV-2048").first()
    res = db.query(ReconciliationResult).filter_by(id=case.reconciliation_result_id).first()

    assert inv.total_amount == Decimal("100000.00"), f"Expected 100,000, got {inv.total_amount}"
    assert inv.subtotal == Decimal("97500.00"), f"Expected 97,500, got {inv.subtotal}"
    assert inv.tax_amount == Decimal("18000.00"), f"Expected 18,000, got {inv.tax_amount}"
    assert res.variance_amount == Decimal("450.00"), f"Expected 450, got {res.variance_amount}"
    assert case.risk_score == Decimal("62.00"), f"Expected 62.00, got {case.risk_score}"
    assert case.priority == "HIGH", f"Expected HIGH, got {case.priority}"

    print("-" * 60)
    print("[OK] Pinned Case Verified:")
    print(f"  * Case Number:        {case.case_number}")
    print(f"  * Vendor:             ABC Supplies (Dispute Count: 2)")
    print(f"  * Invoice Total:      INR 100,000.00")
    print(f"  * Taxable Subtotal:   INR 97,500.00")
    print(f"  * Recorded Tax:       INR 18,000.00")
    print(f"  * Expected Tax (18%): INR 17,550.00")
    print(f"  * Tax Variance:       INR 450.00")
    print(f"  * Risk Score:         {case.risk_score} ({case.priority})")
    print("=" * 60)
    print("DEMO ENVIRONMENT IS FULLY PREPARED AND READY.")
    print("=" * 60)
    db.close()


if __name__ == "__main__":
    reset_demo()
