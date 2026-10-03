import io
import csv
import json
import random
from pathlib import Path
import sys
from datetime import date, timedelta
from decimal import Decimal
import numpy as np
from sqlalchemy.orm import Session

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.models import (
    Organization,
    Vendor,
    Invoice,
    Transaction,
    Payment,
    LedgerEntry,
    TaxRule,
    ImportBatch,
    Case,
    ReconciliationResult,
)

ANCHOR_DATE = date(2026, 3, 15)
FIXED_SEED = 42

VENDORS_LIST = [
    ("ABC Supplies", "abc supplies", "GSTIN-ABC001"),
    ("Apex Global Logistics", "apex global logistics", "GSTIN-APEX02"),
    ("Quantum Tech Services", "quantum tech services", "GSTIN-QT993"),
    ("Vertex Solutions", "vertex solutions", "GSTIN-VTX444"),
    ("Zenith Industrial Corp", "zenith industrial corp", "GSTIN-ZIC555"),
    ("Pinnacle Office Systems", "pinnacle office systems", "GSTIN-POS666"),
    ("OmniCloud Infrastructure", "omnicloud infrastructure", "GSTIN-OCI777"),
    ("Starlight Media Networks", "starlight media networks", "GSTIN-SMN888"),
]


def generate_demo_dataset():
    rng = random.Random(FIXED_SEED)
    np_rng = np.random.default_rng(FIXED_SEED)

    invoices = []
    transactions = []
    payments = []
    ledger_entries = []

    counts = {
        "clean": 0,
        "many_to_one": 0,
        "one_to_many": 0,
        "id_variation": 0,
        "amount_mismatch": 0,
        "within_tolerance": 0,
        "date_mismatch": 0,
        "tax_discrepancy": 0,
        "missing_payment": 0,
        "vendor_spike": 0,
        "unusual_large": 0,
        "duplicate": 0,
    }

    inv_counter = 1000

    def next_inv_num():
        nonlocal inv_counter
        inv_counter += 1
        return f"INV-{inv_counter}"

    # 1. 56 Clean
    for _ in range(56):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[1:])
        inv_num = next_inv_num()
        day_offset = int(np_rng.integers(0, 30))
        inv_date = ANCHOR_DATE - timedelta(days=day_offset)
        subtotal = Decimal(str(int(np_rng.integers(50, 500) * 100)))
        tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
        total = subtotal + tax

        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "clean",
        })
        transactions.append({
            "reference_id": f"TX-{inv_num}", "transaction_date": inv_date + timedelta(days=2),
            "amount": total, "counterparty": v_name, "source": "BANK_FEED",
            "ground_truth_label": "clean", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{inv_num}", "payment_date": inv_date + timedelta(days=2),
            "amount_paid": total, "payment_method": "ACH", "ground_truth_label": "clean", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "clean",
        })
        counts["clean"] += 1

    # 2. 2 Many-to-One (One payment covers two invoices)
    # Total 2 invoices
    m2o_invs = []
    for _ in range(2):
        v_name, v_norm, v_tax = VENDORS_LIST[2]
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=10)
        subtotal = Decimal("20000.00")
        tax = Decimal("3600.00")
        total = Decimal("23600.00")
        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "many_to_one",
        })
        m2o_invs.append(inv_num)
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "many_to_one",
        })
        counts["many_to_one"] += 1

    # Single combined payment & transaction for both invoices
    combined_total = Decimal("47200.00")
    transactions.append({
        "reference_id": f"TX-M2O-{m2o_invs[0]}-{m2o_invs[1]}",
        "transaction_date": ANCHOR_DATE - timedelta(days=5),
        "amount": combined_total, "counterparty": VENDORS_LIST[2][0], "source": "BANK_FEED",
        "ground_truth_label": "many_to_one", "linked_inv": m2o_invs[0],
    })
    payments.append({
        "payment_reference": f"PAY-M2O-{m2o_invs[0]}-{m2o_invs[1]}",
        "payment_date": ANCHOR_DATE - timedelta(days=5),
        "amount_paid": combined_total, "payment_method": "WIRE",
        "ground_truth_label": "many_to_one", "linked_inv": m2o_invs[0],
    })

    # 3. 2 One-to-Many (Invoice paid in 2 parts)
    for _ in range(2):
        v_name, v_norm, v_tax = VENDORS_LIST[3]
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=12)
        subtotal = Decimal("50000.00")
        tax = Decimal("9000.00")
        total = Decimal("59000.00")
        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "one_to_many",
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "one_to_many",
        })
        # Part 1: 50%, Part 2: 50%
        half = Decimal("29500.00")
        for part_idx, days in [(1, 2), (2, 7)]:
            transactions.append({
                "reference_id": f"TX-{inv_num}-P{part_idx}", "transaction_date": inv_date + timedelta(days=days),
                "amount": half, "counterparty": v_name, "source": "BANK_FEED",
                "ground_truth_label": "one_to_many", "linked_inv": inv_num,
            })
            payments.append({
                "payment_reference": f"PAY-{inv_num}-P{part_idx}", "payment_date": inv_date + timedelta(days=days),
                "amount_paid": half, "payment_method": "ACH",
                "ground_truth_label": "one_to_many", "linked_inv": inv_num,
            })
        counts["one_to_many"] += 1

    # 4. 8 Invoice-ID variations (INV-2048, inv 2048, INV2048)
    variations = [
        lambda s: s.lower().replace("-", " "),
        lambda s: s.replace("-", ""),
        lambda s: s.lower().replace("-", ""),
        lambda s: f"REF/{s}",
    ]
    for i in range(8):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[1:])
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=15)
        subtotal = Decimal("15000.00")
        tax = Decimal("2700.00")
        total = Decimal("17700.00")
        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "id_variation",
        })
        var_func = variations[i % len(variations)]
        mangled_ref = var_func(inv_num)
        transactions.append({
            "reference_id": f"TX-{mangled_ref}", "transaction_date": inv_date + timedelta(days=3),
            "amount": total, "counterparty": v_name, "source": "BANK_FEED",
            "ground_truth_label": "id_variation", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{mangled_ref}", "payment_date": inv_date + timedelta(days=3),
            "amount_paid": total, "payment_method": "WIRE",
            "ground_truth_label": "id_variation", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "id_variation",
        })
        counts["id_variation"] += 1

    # 5. 6 Amount mismatches beyond tolerance
    for i in range(6):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[1:])
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=18)
        subtotal = Decimal("30000.00")
        tax = Decimal("5400.00")
        total = Decimal("35400.00")
        mismatched_paid = total - Decimal(str((i + 1) * 250))

        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "amount_mismatch",
        })
        transactions.append({
            "reference_id": f"TX-{inv_num}", "transaction_date": inv_date + timedelta(days=2),
            "amount": mismatched_paid, "counterparty": v_name, "source": "BANK_FEED",
            "ground_truth_label": "amount_mismatch", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{inv_num}", "payment_date": inv_date + timedelta(days=2),
            "amount_paid": mismatched_paid, "payment_method": "ACH",
            "ground_truth_label": "amount_mismatch", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "amount_mismatch",
        })
        counts["amount_mismatch"] += 1

    # 6. 4 Amounts within tolerance (penny variance <= $0.05)
    for i in range(4):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[1:])
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=14)
        subtotal = Decimal("12000.00")
        tax = Decimal("2160.00")
        total = Decimal("14160.00")
        penny_diff = Decimal(f"0.0{i + 1}")
        paid_amount = total - penny_diff

        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "within_tolerance",
        })
        transactions.append({
            "reference_id": f"TX-{inv_num}", "transaction_date": inv_date + timedelta(days=1),
            "amount": paid_amount, "counterparty": v_name, "source": "BANK_FEED",
            "ground_truth_label": "within_tolerance", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{inv_num}", "payment_date": inv_date + timedelta(days=1),
            "amount_paid": paid_amount, "payment_method": "ACH",
            "ground_truth_label": "within_tolerance", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "within_tolerance",
        })
        counts["within_tolerance"] += 1

    # 7. 5 Date mismatches beyond 3 days (e.g. 15-40 days payment lag)
    for i in range(5):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[1:])
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=35)
        pay_date = inv_date + timedelta(days=20 + i * 4)
        subtotal = Decimal("25000.00")
        tax = Decimal("4500.00")
        total = Decimal("29500.00")

        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "date_mismatch",
        })
        transactions.append({
            "reference_id": f"TX-{inv_num}", "transaction_date": pay_date,
            "amount": total, "counterparty": v_name, "source": "BANK_FEED",
            "ground_truth_label": "date_mismatch", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{inv_num}", "payment_date": pay_date,
            "amount_paid": total, "payment_method": "WIRE",
            "ground_truth_label": "date_mismatch", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "date_mismatch",
        })
        counts["date_mismatch"] += 1

    # 8. 6 Tax-rate discrepancies (including the PINNED TX-10482)
    # Case 1: PINNED TX-10482
    pinned_vendor = VENDORS_LIST[0]  # ("ABC Supplies", "abc supplies", "GSTIN-ABC001")
    pinned_inv = "INV-2048"
    pinned_subtotal = Decimal("97500.00")
    pinned_tax_recorded = Decimal("18000.00")
    pinned_total = Decimal("100000.00")
    pinned_inv_date = ANCHOR_DATE - timedelta(days=8)

    invoices.append({
        "vendor_name": pinned_vendor[0], "vendor_norm": pinned_vendor[1], "vendor_tax": pinned_vendor[2],
        "invoice_number": pinned_inv, "normalized_number": "INV2048",
        "invoice_date": pinned_inv_date, "subtotal": pinned_subtotal, "tax_amount": pinned_tax_recorded,
        "total_amount": pinned_total, "ground_truth_label": "tax_discrepancy",
    })
    transactions.append({
        "reference_id": "TX-10482", "transaction_date": pinned_inv_date + timedelta(days=2),
        "amount": pinned_total, "counterparty": pinned_vendor[0], "source": "BANK_FEED",
        "ground_truth_label": "tax_discrepancy", "linked_inv": pinned_inv,
    })
    payments.append({
        "payment_reference": "PAY-TX-10482", "payment_date": pinned_inv_date + timedelta(days=2),
        "amount_paid": pinned_total, "payment_method": "WIRE",
        "ground_truth_label": "tax_discrepancy", "linked_inv": pinned_inv,
    })
    ledger_entries.append({
        "account_code": "2000-AP", "entry_date": pinned_inv_date, "debit": pinned_total, "credit": Decimal("0.00"),
        "reference_id": pinned_inv, "ground_truth_label": "tax_discrepancy",
    })
    counts["tax_discrepancy"] += 1

    # Remaining 5 Tax discrepancies
    for _ in range(5):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[1:])
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=11)
        subtotal = Decimal("50000.00")
        erroneous_tax = Decimal("6000.00")  # Should be 9000 at 18%
        total = Decimal("56000.00")
        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": erroneous_tax,
            "total_amount": total, "ground_truth_label": "tax_discrepancy",
        })
        transactions.append({
            "reference_id": f"TX-{inv_num}", "transaction_date": inv_date + timedelta(days=2),
            "amount": total, "counterparty": v_name, "source": "BANK_FEED",
            "ground_truth_label": "tax_discrepancy", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{inv_num}", "payment_date": inv_date + timedelta(days=2),
            "amount_paid": total, "payment_method": "ACH",
            "ground_truth_label": "tax_discrepancy", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "tax_discrepancy",
        })
        counts["tax_discrepancy"] += 1

    # 9. 5 Missing Payments / Transactions
    for _ in range(5):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[1:])
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=22)
        subtotal = Decimal("40000.00")
        tax = Decimal("7200.00")
        total = Decimal("47200.00")
        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "missing_payment",
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "missing_payment",
        })
        counts["missing_payment"] += 1

    # 10. 3 Vendor-spike invoices (one vendor: Vertex Solutions)
    spike_vendor = VENDORS_LIST[3]
    for _ in range(3):
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=3)
        subtotal = Decimal("150000.00")
        tax = Decimal("27000.00")
        total = Decimal("177000.00")
        invoices.append({
            "vendor_name": spike_vendor[0], "vendor_norm": spike_vendor[1], "vendor_tax": spike_vendor[2],
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "vendor_spike",
        })
        transactions.append({
            "reference_id": f"TX-{inv_num}", "transaction_date": inv_date + timedelta(days=1),
            "amount": total, "counterparty": spike_vendor[0], "source": "BANK_FEED",
            "ground_truth_label": "vendor_spike", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{inv_num}", "payment_date": inv_date + timedelta(days=1),
            "amount_paid": total, "payment_method": "WIRE",
            "ground_truth_label": "vendor_spike", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "vendor_spike",
        })
        counts["vendor_spike"] += 1

    # 11. 3 Unusual large transactions
    for _ in range(3):
        v_name, v_norm, v_tax = rng.choice(VENDORS_LIST[4:])
        inv_num = next_inv_num()
        inv_date = ANCHOR_DATE - timedelta(days=7)
        subtotal = Decimal("750000.00")
        tax = Decimal("135000.00")
        total = Decimal("885000.00")
        invoices.append({
            "vendor_name": v_name, "vendor_norm": v_norm, "vendor_tax": v_tax,
            "invoice_number": inv_num, "normalized_number": inv_num.replace("-", "").upper(),
            "invoice_date": inv_date, "subtotal": subtotal, "tax_amount": tax,
            "total_amount": total, "ground_truth_label": "unusual_large",
        })
        transactions.append({
            "reference_id": f"TX-{inv_num}", "transaction_date": inv_date + timedelta(days=2),
            "amount": total, "counterparty": v_name, "source": "BANK_FEED",
            "ground_truth_label": "unusual_large", "linked_inv": inv_num,
        })
        payments.append({
            "payment_reference": f"PAY-{inv_num}", "payment_date": inv_date + timedelta(days=2),
            "amount_paid": total, "payment_method": "WIRE",
            "ground_truth_label": "unusual_large", "linked_inv": inv_num,
        })
        ledger_entries.append({
            "account_code": "2000-AP", "entry_date": inv_date, "debit": total, "credit": Decimal("0.00"),
            "reference_id": inv_num, "ground_truth_label": "unusual_large",
        })
        counts["unusual_large"] += 1

    # Check: base invoices must equal 100
    base_count = len(invoices)
    assert base_count == 100, f"Expected 100 base invoices, got {base_count}"

    # 12. 5 Duplicate invoice rows added on top
    for i in range(5):
        dup = dict(invoices[i])
        dup["ground_truth_label"] = "duplicate"
        invoices.append(dup)
        counts["duplicate"] += 1

    total_invoice_rows = len(invoices)
    assert total_invoice_rows == 105, f"Expected 105 total invoices, got {total_invoice_rows}"

    dataset = {
        "metadata": {
            "seed": FIXED_SEED,
            "anchor_date": ANCHOR_DATE.isoformat(),
            "total_invoices": total_invoice_rows,
            "base_invoices": base_count,
            "counts": counts,
            "pinned_case": {
                "transaction_id": "TX-10482",
                "invoice_number": "INV-2048",
                "vendor": "ABC Supplies",
                "taxable": 97500.00,
                "statutory_rate": 0.18,
                "expected_tax": 17550.00,
                "recorded_tax": 18000.00,
                "variance": 450.00,
                "invoice_total": 100000.00,
                "payment_amount": 100000.00,
            }
        },
        "invoices": invoices,
        "transactions": transactions,
        "payments": payments,
        "ledger_entries": ledger_entries,
    }

    # Generate canonical deterministic CSV string
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([
        "invoice_number", "vendor_name", "invoice_date", "subtotal",
        "tax_amount", "total_amount", "ground_truth_label"
    ])
    for inv in invoices:
        writer.writerow([
            inv["invoice_number"], inv["vendor_name"], inv["invoice_date"].isoformat(),
            str(inv["subtotal"]), str(inv["tax_amount"]), str(inv["total_amount"]),
            inv["ground_truth_label"]
        ])

    csv_data = output.getvalue()
    return dataset, csv_data


def seed_demo_data_to_db(db: Session) -> dict:
    dataset, _ = generate_demo_dataset()

    # 1. Ensure Organization
    org = db.query(Organization).filter_by(slug="taxpulse-org").first()
    if not org:
        org = Organization(
            name="TaxPulse Global Enterprises",
            slug="taxpulse-org",
            tax_identifier="GSTIN-27AAACT2727Q1ZB",
        )
        db.add(org)
        db.flush()

    # Seed demo users if not present
    from app.models.models import User
    from app.services.auth import hash_password
    demo_users = [
        ("admin@taxpulse.com", "Admin User", "ADMIN", "+919876543200"),
        ("reviewer@taxpulse.com", "Senior Reviewer", "REVIEWER", "+919876543210"),
        ("accountant@taxpulse.com", "Lead Accountant", "ACCOUNTANT", "+919876543220"),
        ("viewer@taxpulse.com", "Audit Viewer", "VIEWER", "+919876543230"),
    ]
    for email, name, role, phone in demo_users:
        if not db.query(User).filter_by(organization_id=org.id, email=email).first():
            u = User(
                organization_id=org.id,
                email=email,
                password_hash=hash_password("DemoPassword123!"),
                full_name=name,
                role=role,
                phone_number=phone,
            )
            db.add(u)
    db.flush()

    # 2. Delete previous demo data for idempotency in child-to-parent order
    from app.models.models import Anomaly, ReconciliationRun
    db.query(Case).filter_by(organization_id=org.id).delete()
    db.query(Anomaly).filter_by(organization_id=org.id).delete()
    db.query(ReconciliationResult).filter_by(organization_id=org.id).delete()
    db.query(ReconciliationRun).filter_by(organization_id=org.id).delete()
    db.query(Payment).filter_by(organization_id=org.id).delete()
    db.query(Invoice).filter_by(organization_id=org.id).delete()
    db.query(Transaction).filter_by(organization_id=org.id).delete()
    db.query(LedgerEntry).filter_by(organization_id=org.id).delete()
    db.query(ImportBatch).filter_by(organization_id=org.id).delete()
    db.flush()

    # 3. Cache/Create Vendors
    vendor_map = {}
    for v_name, v_norm, v_tax in VENDORS_LIST:
        v = db.query(Vendor).filter_by(organization_id=org.id, name=v_name).first()
        disputes = 2 if v_name == "ABC Supplies" else 0
        tier = "MEDIUM" if v_name == "ABC Supplies" else "LOW"
        if not v:
            v = Vendor(
                organization_id=org.id,
                name=v_name,
                normalized_name=v_norm,
                tax_identifier=v_tax,
                risk_tier=tier,
                dispute_count=disputes,
            )
            db.add(v)
            db.flush()
        else:
            v.dispute_count = disputes
            v.risk_tier = tier
            db.flush()
        vendor_map[v_name] = v.id

    # 4. Insert Invoices
    inv_id_map = {}
    for inv_data in dataset["invoices"]:
        v_id = vendor_map[inv_data["vendor_name"]]
        inv = Invoice(
            organization_id=org.id,
            vendor_id=v_id,
            invoice_number=inv_data["invoice_number"],
            normalized_number=inv_data["normalized_number"],
            invoice_date=inv_data["invoice_date"],
            currency="USD",
            subtotal=inv_data["subtotal"],
            tax_amount=inv_data["tax_amount"],
            total_amount=inv_data["total_amount"],
            status="PENDING",
            ground_truth_label=inv_data["ground_truth_label"],
        )
        db.add(inv)
        db.flush()
        inv_id_map[inv_data["invoice_number"]] = inv.id

    # 5. Insert Transactions
    for txn_data in dataset["transactions"]:
        txn = Transaction(
            organization_id=org.id,
            source=txn_data["source"],
            reference_id=txn_data["reference_id"],
            transaction_date=txn_data["transaction_date"],
            amount=txn_data["amount"],
            currency="USD",
            description=f"Payment for {txn_data.get('linked_inv', 'invoice')}",
            counterparty_name=txn_data["counterparty"],
            ground_truth_label=txn_data["ground_truth_label"],
        )
        db.add(txn)

    # 6. Insert Payments
    for pmt_data in dataset["payments"]:
        linked_id = inv_id_map.get(pmt_data.get("linked_inv"))
        pmt = Payment(
            organization_id=org.id,
            invoice_id=linked_id,
            payment_reference=pmt_data["payment_reference"],
            payment_date=pmt_data["payment_date"],
            amount_paid=pmt_data["amount_paid"],
            payment_method=pmt_data["payment_method"],
            status="COMPLETED",
            ground_truth_label=pmt_data["ground_truth_label"],
        )
        db.add(pmt)

    # 7. Insert Ledger Entries
    for led_data in dataset["ledger_entries"]:
        led = LedgerEntry(
            organization_id=org.id,
            account_code=led_data["account_code"],
            entry_date=led_data["entry_date"],
            debit=led_data["debit"],
            credit=led_data["credit"],
            reference_id=led_data["reference_id"],
            description="Accounts Payable Journal",
        )
        db.add(led)

    # 8. Ensure Batch and Rules
    batch = ImportBatch(
        organization_id=org.id,
        source_type="CSV",
        file_name="demo_reconciliation_batch.csv",
        file_hash="demo-seed-42-hash",
        row_count=len(dataset["invoices"]),
        status="PARSED",
    )
    db.add(batch)

    # Ensure 18% tax rule
    rule = db.query(TaxRule).filter_by(organization_id=org.id, tax_type="GST", rate=Decimal("0.1800")).first()
    if not rule:
        rule = TaxRule(
            organization_id=org.id,
            tax_type="GST",
            jurisdiction="IN-MH",
            rate=Decimal("0.1800"),
            effective_from=date(2024, 1, 1),
            is_active=True,
            is_demo=True,
        )
        db.add(rule)

    db.commit()
    return dataset["metadata"]


def main():
    dataset, csv_content = generate_demo_dataset()

    # Write expected_results.json fixture
    fixture_dir = BASE_DIR / "tests" / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / "expected_results.json"
    with open(fixture_path, "w", encoding="utf-8") as f:
        # Convert Decimals and dates to strings for JSON
        serializable = {
            "metadata": dataset["metadata"],
            "summary": {
                "invoices_count": len(dataset["invoices"]),
                "transactions_count": len(dataset["transactions"]),
                "payments_count": len(dataset["payments"]),
                "ledger_entries_count": len(dataset["ledger_entries"]),
            }
        }
        json.dump(serializable, f, indent=2)
    print(f"Wrote expected results to {fixture_path}")
    print(f"Generated {len(dataset['invoices'])} invoices ({dataset['metadata']['base_invoices']} base + 5 duplicates).")
    print(f"Pinned case: {dataset['metadata']['pinned_case']}")


if __name__ == "__main__":
    main()
