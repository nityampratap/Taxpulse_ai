"""
TaxPulse AI - Synthetic Evaluation Script
Computes measured precision and recall per injected ground-truth label on the deterministic test dataset.
DISCLAIMER: Reported on synthetic injected labels only; real-world precision and recall may differ.
"""
import sys
from pathlib import Path
from decimal import Decimal

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal, engine, Base
from app.models.models import Organization, ReconciliationResult, Case, Anomaly
from scripts.generate_demo_data import seed_demo_data_to_db
from app.services.reconciliation.engine import ReconciliationEngine
from app.services.anomaly import AnomalyDetector
from app.services.cases import CaseService


def run_evaluation():
    print("=" * 70)
    print(" TAXPULSE AI - SYNTHETIC DATA EVALUATION")
    print("=" * 70)

    # 1. Initialize fresh DB session
    Base.metadata.create_all(engine)
    db = SessionLocal()

    # Clear tables
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()

    # 2. Seed deterministic demo data (seed=42)
    meta = seed_demo_data_to_db(db)
    db.commit()
    print(f"Generated {meta['total_invoices']} invoices across 12 injection categories.")

    # 3. Execute reconciliation engine
    org = db.query(Organization).first()
    engine_svc = ReconciliationEngine()
    run = engine_svc.run(db, org.id)
    db.commit()

    results = db.query(ReconciliationResult).filter_by(run_id=run.id).all()
    AnomalyDetector().detect(db, org.id, results)
    cases = CaseService().create_cases_from_results(db, org.id, results)
    db.commit()

    # 4. Map expected status per label
    expected_status_map = {
        "clean": "MATCHED",
        "many_to_one": "PARTIAL_MATCH",
        "one_to_many": "PARTIAL_MATCH",
        "id_variation": "MATCHED",
        "amount_mismatch": "MISMATCH",
        "within_tolerance": "MATCHED_WITH_TOLERANCE",
        "date_mismatch": "MISMATCH",
        "tax_discrepancy": "TAX_VARIANCE",
        "missing_payment": "MISSING",
        "vendor_spike": "MATCHED",
        "unusual_large": "MATCHED",
        "duplicate": "DUPLICATE",
    }

    # 5. Compute metrics per label
    metrics = {}
    for label, target_status in expected_status_map.items():
        tp = 0
        fp = 0
        fn = 0
        for r in results:
            actual_label = r.ground_truth_label
            detected_status = r.status

            if actual_label == label and detected_status == target_status:
                tp += 1
            elif actual_label != label and detected_status == target_status:
                fp += 1
            elif actual_label == label and detected_status != target_status:
                fn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics[label] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall, "f1": f1,
        }

    # Print Table
    print(f"\n{'Label':<20} | {'Expected':<22} | {'TP':<4} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 88)

    macro_p = 0.0
    macro_r = 0.0
    macro_f1 = 0.0

    for label, data in metrics.items():
        exp = expected_status_map[label]
        print(f"{label:<20} | {exp:<22} | {data['tp']:<4} | {data['precision']:<10.2%} | {data['recall']:<10.2%} | {data['f1']:<10.2%}")
        macro_p += data["precision"]
        macro_r += data["recall"]
        macro_f1 += data["f1"]

    n = len(metrics)
    macro_p /= n
    macro_r /= n
    macro_f1 /= n

    print("-" * 88)
    print(f"{'MACRO AVERAGE':<20} | {'--':<22} | {'--':<4} | {macro_p:<10.2%} | {macro_r:<10.2%} | {macro_f1:<10.2%}")
    print("=" * 88)
    print("DISCLAIMER: Reported on synthetic injected labels only; real-world precision and recall may differ.")
    print("=" * 88)

    db.close()


if __name__ == "__main__":
    run_evaluation()
