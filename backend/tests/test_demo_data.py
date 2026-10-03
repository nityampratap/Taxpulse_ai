import hashlib
import json
from pathlib import Path
from decimal import Decimal
import pytest
from scripts.generate_demo_data import generate_demo_dataset


def test_deterministic_csv_generation():
    """Verify deterministic byte-identical CSV generation across independent runs."""
    dataset1, csv1 = generate_demo_dataset()
    dataset2, csv2 = generate_demo_dataset()

    assert csv1 == csv2, "CSV output must be identical across separate generation runs"

    hash1 = hashlib.sha256(csv1.encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(csv2.encode("utf-8")).hexdigest()
    assert hash1 == hash2, "SHA256 hashes of generated CSVs must match"

    lines = csv1.strip().split("\n")
    # 1 header + 105 invoice rows = 106 lines
    assert len(lines) == 106, f"Expected 106 CSV lines (1 header + 105 rows), got {len(lines)}"
    assert lines[0] == "invoice_number,vendor_name,invoice_date,subtotal,tax_amount,total_amount,ground_truth_label"


def test_exact_category_counts():
    """Verify the exact ground truth count breakdown matching the specification."""
    dataset, _ = generate_demo_dataset()
    invoices = dataset["invoices"]
    counts = dataset["metadata"]["counts"]

    expected_breakdown = {
        "clean": 56,
        "many_to_one": 2,
        "one_to_many": 2,
        "id_variation": 8,
        "amount_mismatch": 6,
        "within_tolerance": 4,
        "date_mismatch": 5,
        "tax_discrepancy": 6,
        "missing_payment": 5,
        "vendor_spike": 3,
        "unusual_large": 3,
        "duplicate": 5,
    }

    assert counts == expected_breakdown

    # Verify actual invoice list matches counts per label
    actual_counts = {}
    for inv in invoices:
        lbl = inv["ground_truth_label"]
        actual_counts[lbl] = actual_counts.get(lbl, 0) + 1

    assert actual_counts == expected_breakdown
    assert dataset["metadata"]["base_invoices"] == 100
    assert dataset["metadata"]["total_invoices"] == 105
    assert len(invoices) == 105


def test_pinned_case_tx10482():
    """Verify pinned tax-rate case TX-10482 ABC Supplies INV-2048."""
    dataset, _ = generate_demo_dataset()
    pinned = dataset["metadata"]["pinned_case"]

    assert pinned["transaction_id"] == "TX-10482"
    assert pinned["invoice_number"] == "INV-2048"
    assert pinned["vendor"] == "ABC Supplies"
    assert pinned["taxable"] == 97500.00
    assert pinned["statutory_rate"] == 0.18
    assert pinned["expected_tax"] == 17550.00
    assert pinned["recorded_tax"] == 18000.00
    assert pinned["variance"] == 450.00
    assert pinned["invoice_total"] == 100000.00
    assert pinned["payment_amount"] == 100000.00

    # Ensure pinned invoice exists in invoices list
    pinned_inv = next(
        (inv for inv in dataset["invoices"] if inv["invoice_number"] == "INV-2048"),
        None,
    )
    assert pinned_inv is not None
    assert pinned_inv["vendor_name"] == "ABC Supplies"
    assert pinned_inv["subtotal"] == Decimal("97500.00")
    assert pinned_inv["tax_amount"] == Decimal("18000.00")
    assert pinned_inv["total_amount"] == Decimal("100000.00")
    assert pinned_inv["ground_truth_label"] == "tax_discrepancy"

    # Ensure pinned transaction exists
    pinned_txn = next(
        (tx for tx in dataset["transactions"] if tx["reference_id"] == "TX-10482"),
        None,
    )
    assert pinned_txn is not None
    assert pinned_txn["counterparty"] == "ABC Supplies"
    assert pinned_txn["amount"] == Decimal("100000.00")
    assert pinned_txn["ground_truth_label"] == "tax_discrepancy"


def test_fixture_expected_results_file():
    """Verify tests/fixtures/expected_results.json exists and is consistent with generator."""
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "expected_results.json"
    assert fixture_path.exists(), "expected_results.json fixture must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dataset, _ = generate_demo_dataset()
    assert data["metadata"]["counts"] == dataset["metadata"]["counts"]
    assert data["metadata"]["pinned_case"] == dataset["metadata"]["pinned_case"]
    assert data["summary"]["invoices_count"] == 105


def test_demo_api_endpoints(client):
    """Test POST /api/demo/generate and POST /api/demo/reset."""
    # Test generation
    gen_resp = client.post("/api/demo/generate")
    assert gen_resp.status_code == 201
    gen_data = gen_resp.json()
    assert gen_data["status"] == "success"
    assert gen_data["metadata"]["total_invoices"] == 105
    assert gen_data["metadata"]["pinned_case"]["transaction_id"] == "TX-10482"

    # Test reset
    reset_resp = client.post("/api/demo/reset")
    assert reset_resp.status_code == 200
    reset_data = reset_resp.json()
    assert reset_data["status"] == "success"

    # Also test /api/v1/demo/generate and reset
    gen_v1 = client.post("/api/v1/demo/generate")
    assert gen_v1.status_code == 201
    reset_v1 = client.post("/api/v1/demo/reset")
    assert reset_v1.status_code == 200


def test_reconciliation_per_label_detection(db):
    """Assert every injected label in expected_results.json is detected with intended status/reason."""
    from scripts.generate_demo_data import seed_demo_data_to_db
    from app.services.reconciliation.engine import ReconciliationEngine
    from app.services.anomaly import AnomalyDetector
    from app.services.cases import CaseService
    from app.models.models import Organization, ReconciliationResult, Case, Anomaly

    fixture_path = Path(__file__).resolve().parent / "fixtures" / "expected_results.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # 1. Seed demo data
    seed_demo_data_to_db(db)
    db.commit()

    # 2. Run reconciliation
    org = db.query(Organization).first()
    engine = ReconciliationEngine()
    run = engine.run(db, org.id)
    db.commit()

    results = db.query(ReconciliationResult).filter_by(run_id=run.id).all()
    assert len(results) == 105

    # 3. Run anomaly detector & case creation
    AnomalyDetector().detect(db, org.id, results)
    cases = CaseService().create_cases_from_results(db, org.id, results)
    db.commit()

    # 4. Group results by ground_truth_label
    by_label = {}
    for r in results:
        by_label.setdefault(r.ground_truth_label, []).append(r)

    # 5. Assert each label meets spec
    for label, expected in spec["expected_detection"].items():
        assert label in by_label, f"Label {label} not detected in any result!"
        label_results = by_label[label]
        assert len(label_results) == expected["count"], f"Label {label}: expected {expected['count']} items, got {len(label_results)}"

        for r in label_results:
            assert r.status == expected["expected_status"], f"Label {label} id {r.invoice_id}: expected status {expected['expected_status']}, got {r.status}"
            if "reason_code" in expected:
                reasons = r.reason_codes or []
                assert expected["reason_code"] in reasons, f"Label {label}: expected reason {expected['reason_code']} in {reasons}"
            if "match_method" in expected:
                assert r.match_method == expected["match_method"], f"Label {label}: expected method {expected['match_method']}, got {r.match_method}"


def test_pinned_case_tx10482_pipeline(db):
    """Verify pinned case TX-10482 end-to-end: numbers, status, risk score, factors."""
    from scripts.generate_demo_data import seed_demo_data_to_db
    from app.services.reconciliation.engine import ReconciliationEngine
    from app.services.anomaly import AnomalyDetector
    from app.services.cases import CaseService
    from app.models.models import Organization, ReconciliationResult, Case, Invoice

    seed_demo_data_to_db(db)
    db.commit()

    org = db.query(Organization).first()
    engine = ReconciliationEngine()
    run = engine.run(db, org.id)
    db.commit()

    results = db.query(ReconciliationResult).filter_by(run_id=run.id).all()
    AnomalyDetector().detect(db, org.id, results)
    cases = CaseService().create_cases_from_results(db, org.id, results)
    db.commit()

    # Verify INV-2048 result
    inv = db.query(Invoice).filter_by(invoice_number="INV-2048").first()
    assert inv is not None
    assert inv.subtotal == Decimal("97500.00")
    assert inv.tax_amount == Decimal("18000.00")
    assert inv.total_amount == Decimal("100000.00")

    result = db.query(ReconciliationResult).filter_by(invoice_id=inv.id).first()
    assert result is not None
    assert result.status == "TAX_VARIANCE"
    assert result.variance_amount == Decimal("450.00")
    assert "TAX_DISCREPANCY" in (result.reason_codes or [])

    # Verify Case TX-10482
    case = db.query(Case).filter_by(case_number="TX-10482").first()
    assert case is not None
    assert case.priority == "HIGH"
    assert case.risk_score == Decimal("62.00")
    assert case.financial_exposure == Decimal("100000.00")
    assert case.tax_impact == Decimal("450.00")

    factor_points = {f["factor"]: f["points"] for f in case.factor_breakdown["factors"]}
    assert factor_points["mismatch_severity"] == 15.0
    assert factor_points["financial_exposure"] == 15.0
    assert factor_points["tax_impact"] == 10.0
    assert factor_points["anomaly_score"] == 12.0
    assert factor_points["vendor_history"] == 5.0
    assert factor_points["recurrence"] == 5.0


