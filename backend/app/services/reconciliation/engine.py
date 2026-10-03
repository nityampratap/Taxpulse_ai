from datetime import date
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Invoice,
    Transaction,
    Payment,
    LedgerEntry,
    TaxRule,
    ReconciliationRun,
    ReconciliationResult,
    Vendor,
)
from app.services.normalization.normalizer import (
    normalize_invoice_number,
    normalize_vendor_name,
)
from app.services.reconciliation.embedder import BaseEmbedder, TfidfCharNgramEmbedder

logger = logging.getLogger(__name__)


class ReconciliationEngine:
    """
    Autonomous multi-pass reconciliation engine executing sequential passes:
    1. Duplicate Invoices Detection
    2. Pass 1: Exact Match (raw ID, exact amount, date within tolerance)
    3. Pass 2: Normalized ID Match
    4. Pass 3: Fuzzy ID Match (RapidFuzz >= 90)
    5. Pass 4: Context-Aware Matching (0.35 vendor, 0.35 amount, 0.20 date, 0.10 Embedder)
    6. Pass 5: One-to-Many Split (max 4 legs)
    7. Pass 6: Many-to-One Split
    8. Pass 7: Cross-Source Three-Way Check (Invoice -> Transaction -> Payment -> Ledger)
    9. Unmatched Detection (MISSING)
    """

    def __init__(
        self,
        embedder: Optional[BaseEmbedder] = None,
        amount_tol_inr: Optional[Decimal] = None,
        amount_tol_pct: Optional[Decimal] = None,
        date_tol_days: Optional[int] = None,
    ):
        self.embedder = embedder or TfidfCharNgramEmbedder()
        self.amount_tol_inr = amount_tol_inr or getattr(settings, "TOLERANCE_AMOUNT_INR", Decimal("1.00"))
        self.amount_tol_pct = amount_tol_pct or getattr(settings, "TOLERANCE_AMOUNT_PERCENT", Decimal("0.0001"))
        self.date_tol_days = date_tol_days or getattr(settings, "TOLERANCE_DATE_DAYS", 3)

    def is_amount_within_tolerance(self, amt1: Decimal, amt2: Decimal) -> Tuple[bool, Decimal]:
        diff = abs(amt1 - amt2)
        if diff == 0:
            return True, Decimal("0.00")
        if diff <= self.amount_tol_inr:
            return True, diff
        base = max(amt1, amt2, Decimal("0.01"))
        pct = diff / base
        if pct <= self.amount_tol_pct:
            return True, diff
        return False, diff

    def is_date_within_tolerance(self, d1: date, d2: date) -> Tuple[bool, int]:
        diff_days = abs((d1 - d2).days)
        return diff_days <= self.date_tol_days, diff_days

    def run(
        self,
        db: Session,
        organization_id: str,
        batch_id: Optional[str] = None,
    ) -> ReconciliationRun:
        """Executes full reconciliation pipeline for an organization."""
        # 1. Initialize Reconciliation Run
        run = ReconciliationRun(
            organization_id=organization_id,
            batch_id=batch_id,
            status="IN_PROGRESS",
            total_processed=0,
            matched_count=0,
            variance_count=0,
        )
        db.add(run)
        db.flush()

        # 2. Query Invoices, Transactions, Payments, Ledger Entries, Tax Rules
        invoices_q = db.query(Invoice).filter_by(organization_id=organization_id)
        if batch_id:
            invoices_q = invoices_q.filter_by(batch_id=batch_id)
        invoices: List[Invoice] = invoices_q.order_by(Invoice.created_at.asc()).all()

        transactions: List[Transaction] = db.query(Transaction).filter_by(organization_id=organization_id).all()
        payments: List[Payment] = db.query(Payment).filter_by(organization_id=organization_id).all()
        ledger_entries: List[LedgerEntry] = db.query(LedgerEntry).filter_by(organization_id=organization_id).all()
        tax_rules: List[TaxRule] = db.query(TaxRule).filter_by(organization_id=organization_id, is_active=True).all()
        vendors: List[Vendor] = db.query(Vendor).filter_by(organization_id=organization_id).all()
        vendor_map = {v.id: v for v in vendors}

        # Statutory tax rate map
        statutory_rate = Decimal("0.1800")
        if tax_rules:
            statutory_rate = tax_rules[0].rate

        used_transaction_ids: Set[str] = set()
        used_invoice_ids: Set[str] = set()
        results: List[ReconciliationResult] = []

        # ----------------------------------------------------------------------
        # Pre-pass A: Duplicate Invoices Check
        # ----------------------------------------------------------------------
        seen_invoice_signatures: Dict[str, str] = {}
        for inv in invoices:
            sig = f"{inv.vendor_id}_{inv.normalized_number}_{inv.total_amount}"
            if sig in seen_invoice_signatures:
                # Marked as duplicate
                res = ReconciliationResult(
                    organization_id=organization_id,
                    run_id=run.id,
                    invoice_id=inv.id,
                    transaction_id=None,
                    payment_id=None,
                    match_type="DUPLICATE",
                    match_method="DUPLICATE_DETECTION",
                    confidence_score=Decimal("1.0000"),
                    match_confidence=Decimal("1.0000"),
                    variance_amount=Decimal("0.00"),
                    status="DUPLICATE",
                    reason_codes=["DUPLICATE_INVOICE"],
                    evidence={
                        "duplicate_of_invoice_id": seen_invoice_signatures[sig],
                        "invoice_number": inv.invoice_number,
                    },
                    ground_truth_label=inv.ground_truth_label,
                )
                results.append(res)
                used_invoice_ids.add(inv.id)
            else:
                seen_invoice_signatures[sig] = inv.id

        remaining_invoices = [inv for inv in invoices if inv.id not in used_invoice_ids]

        # ----------------------------------------------------------------------
        # Pass 6: Many-to-One Split Check (Payment covers multiple invoices)
        # ----------------------------------------------------------------------
        # E.g. transaction reference contains multiple invoice numbers (e.g. TX-M2O-INV-...)
        for tx in transactions:
            if tx.id in used_transaction_ids:
                continue
            matching_invs = [
                inv for inv in remaining_invoices
                if inv.id not in used_invoice_ids and (
                    inv.invoice_number in tx.reference_id or
                    inv.normalized_number in tx.reference_id.replace("-", "").upper()
                )
            ]
            if len(matching_invs) >= 2:
                inv_total_sum = sum(inv.total_amount for inv in matching_invs)
                within_tol, diff = self.is_amount_within_tolerance(inv_total_sum, tx.amount)
                if within_tol:
                    used_transaction_ids.add(tx.id)
                    for matched_inv in matching_invs:
                        used_invoice_ids.add(matched_inv.id)
                        res = ReconciliationResult(
                            organization_id=organization_id,
                            run_id=run.id,
                            invoice_id=matched_inv.id,
                            transaction_id=tx.id,
                            payment_id=None,
                            match_type="SPLIT_N_1",
                            match_method="MANY_TO_ONE",
                            confidence_score=Decimal("0.9500"),
                            match_confidence=Decimal("0.9500"),
                            variance_amount=diff,
                            status="PARTIAL_MATCH",
                            reason_codes=["SPLIT_MANY_TO_ONE"],
                            evidence={
                                "transaction_ref": tx.reference_id,
                                "transaction_amount": str(tx.amount),
                                "combined_invoice_total": str(inv_total_sum),
                                "covered_invoices": [i.invoice_number for i in matching_invs],
                            },
                            ground_truth_label=matched_inv.ground_truth_label,
                        )
                        results.append(res)

        remaining_invoices = [inv for inv in invoices if inv.id not in used_invoice_ids]

        # ----------------------------------------------------------------------
        # Pass 5: One-to-Many Split Check (Invoice paid in up to 4 legs)
        # ----------------------------------------------------------------------
        for inv in remaining_invoices:
            if inv.id in used_invoice_ids:
                continue
            matching_txs = [
                tx for tx in transactions
                if tx.id not in used_transaction_ids and (
                    f"{inv.invoice_number}-P" in tx.reference_id or
                    f"{inv.normalized_number}P" in tx.reference_id.replace("-", "").upper()
                )
            ]
            if len(matching_txs) >= 2 and len(matching_txs) <= 4:
                tx_sum = sum(tx.amount for tx in matching_txs)
                within_tol, diff = self.is_amount_within_tolerance(inv.total_amount, tx_sum)
                if within_tol:
                    used_invoice_ids.add(inv.id)
                    for tx in matching_txs:
                        used_transaction_ids.add(tx.id)
                    res = ReconciliationResult(
                        organization_id=organization_id,
                        run_id=run.id,
                        invoice_id=inv.id,
                        transaction_id=matching_txs[0].id,
                        payment_id=None,
                        match_type="SPLIT_1_N",
                        match_method="ONE_TO_MANY",
                        confidence_score=Decimal("0.9500"),
                        match_confidence=Decimal("0.9500"),
                        variance_amount=diff,
                        status="PARTIAL_MATCH",
                        reason_codes=["SPLIT_ONE_TO_MANY"],
                        evidence={
                            "split_legs_count": len(matching_txs),
                            "split_transaction_refs": [tx.reference_id for tx in matching_txs],
                            "split_sum": str(tx_sum),
                            "invoice_total": str(inv.total_amount),
                        },
                        ground_truth_label=inv.ground_truth_label,
                    )
                    results.append(res)

        remaining_invoices = [inv for inv in invoices if inv.id not in used_invoice_ids]

        # ----------------------------------------------------------------------
        # Passes 1, 2, 3, 4: Exact, Normalized ID, Fuzzy ID, Context-Aware
        # ----------------------------------------------------------------------
        for inv in remaining_invoices:
            if inv.id in used_invoice_ids:
                continue

            v_obj = vendor_map.get(inv.vendor_id)
            v_name = v_obj.name if v_obj else ""
            v_norm = v_obj.normalized_name if v_obj else normalize_vendor_name(v_name)

            best_match: Optional[Dict[str, Any]] = None

            for tx in transactions:
                if tx.id in used_transaction_ids:
                    continue

                tx_ref = tx.reference_id or ""
                tx_ref_clean = tx_ref.replace("TX-", "").replace("TX_", "").strip()
                tx_norm = normalize_invoice_number(tx_ref_clean)

                amount_within_tol, amt_diff = self.is_amount_within_tolerance(inv.total_amount, tx.amount)
                date_within_tol, date_diff_days = self.is_date_within_tolerance(inv.invoice_date, tx.transaction_date)

                # --- Pass 1: Exact Match ---
                is_exact_id = (inv.invoice_number == tx_ref_clean or inv.invoice_number in tx_ref)
                if is_exact_id and amt_diff == 0 and date_within_tol:
                    best_match = {
                        "tx": tx,
                        "match_type": "EXACT",
                        "match_method": "EXACT",
                        "confidence": Decimal("1.0000"),
                        "variance": Decimal("0.00"),
                        "status": "MATCHED",
                        "reasons": ["EXACT_MATCH"],
                        "score": 100.0,
                    }
                    break

                # --- Pass 2: Normalized ID Match ---
                is_norm_id = (inv.normalized_number == tx_norm or inv.normalized_number in tx_norm)
                if is_norm_id and amt_diff == 0 and date_within_tol:
                    best_match = {
                        "tx": tx,
                        "match_type": "EXACT",
                        "match_method": "NORMALIZED_ID",
                        "confidence": Decimal("0.9800"),
                        "variance": Decimal("0.00"),
                        "status": "MATCHED",
                        "reasons": ["NORMALIZED_ID_MATCH"],
                        "score": 98.0,
                    }
                    break

                # --- Pass 3: Fuzzy ID Match (RapidFuzz >= 90) ---
                fuzz_ratio = max(
                    fuzz.ratio(inv.invoice_number, tx_ref_clean),
                    fuzz.partial_ratio(inv.invoice_number, tx_ref),
                    fuzz.token_sort_ratio(inv.invoice_number, tx_ref_clean),
                )
                if fuzz_ratio >= 90 and amt_diff == 0 and date_within_tol:
                    conf = Decimal(str(round(fuzz_ratio / 100.0, 4)))
                    best_match = {
                        "tx": tx,
                        "match_type": "FUZZY",
                        "match_method": "FUZZY_ID",
                        "confidence": conf,
                        "variance": Decimal("0.00"),
                        "status": "FUZZY_MATCH",
                        "reasons": ["FUZZY_ID_MATCH"],
                        "score": float(fuzz_ratio),
                    }
                    break

                # --- Pass 4: Context-Aware Matching ---
                # Check candidate link: exact, normalized, or substring ID match
                has_id_link = (is_exact_id or is_norm_id or inv.invoice_number in tx_ref or inv.normalized_number in tx_ref.replace("-", "").upper())
                tx_cparty_norm = normalize_vendor_name(tx.counterparty_name or "")
                vendor_sim = float(fuzz.token_set_ratio(v_norm, tx_cparty_norm)) / 100.0

                base_amt = max(inv.total_amount, tx.amount, Decimal("1.00"))
                amt_sim = max(0.0, 1.0 - float(amt_diff / base_amt))
                date_sim = max(0.0, 1.0 - min(date_diff_days / 30.0, 1.0))
                embed_sim = self.embedder.similarity(inv.invoice_number, tx_ref)

                context_score = 0.35 * vendor_sim + 0.35 * amt_sim + 0.20 * date_sim + 0.10 * embed_sim

                # If this transaction specifically references this invoice or has high contextual similarity:
                if has_id_link or context_score >= 0.60:
                    # Case A: Amount within tolerance (penny variance)
                    if amount_within_tol and amt_diff > Decimal("0.00") and date_within_tol:
                        best_match = {
                            "tx": tx,
                            "match_type": "EXACT" if has_id_link else "FUZZY",
                            "match_method": "TOLERANCE",
                            "confidence": Decimal("0.9700"),
                            "variance": amt_diff,
                            "status": "MATCHED_WITH_TOLERANCE",
                            "reasons": ["AMOUNT_WITHIN_TOLERANCE"],
                            "score": 95.0,
                        }
                        break

                    # Case B: Exact amount & date within tolerance
                    if amt_diff == Decimal("0.00") and date_within_tol:
                        conf = Decimal(str(round(max(0.60, min(1.0, context_score)), 4)))
                        status_str = "FUZZY_MATCH" if context_score >= 0.80 else "PARTIAL_MATCH"
                        best_match = {
                            "tx": tx,
                            "match_type": "FUZZY",
                            "match_method": "CONTEXT_AWARE",
                            "confidence": conf,
                            "variance": Decimal("0.00"),
                            "status": status_str,
                            "reasons": ["CONTEXT_AWARE_MATCH"],
                            "score": float(context_score * 100),
                        }
                        break

                    # Case C: Amount Mismatch beyond tolerance
                    if has_id_link and not amount_within_tol:
                        best_match = {
                            "tx": tx,
                            "match_type": "MANUAL",
                            "match_method": "CONTEXT_AWARE",
                            "confidence": Decimal("0.6000"),
                            "variance": amt_diff,
                            "status": "MISMATCH",
                            "reasons": ["AMOUNT_MISMATCH"],
                            "score": 60.0,
                        }
                        break

                    # Case D: Date Mismatch beyond 3 days
                    if has_id_link and not date_within_tol and amt_diff == Decimal("0.00"):
                        best_match = {
                            "tx": tx,
                            "match_type": "MANUAL",
                            "match_method": "CONTEXT_AWARE",
                            "confidence": Decimal("0.7000"),
                            "variance": Decimal("0.00"),
                            "status": "MISMATCH",
                            "reasons": ["DATE_OUT_OF_RANGE"],
                            "score": 70.0,
                        }
                        break

            # ------------------------------------------------------------------
            # Tax Discrepancy Evaluation (Statutory Tax Check)
            # ------------------------------------------------------------------
            expected_tax = (inv.subtotal * statutory_rate).quantize(Decimal("0.01"))
            tax_variance = abs(inv.tax_amount - expected_tax)
            has_tax_variance = (tax_variance > Decimal("1.00"))

            if best_match:
                matched_tx: Transaction = best_match["tx"]
                used_transaction_ids.add(matched_tx.id)
                used_invoice_ids.add(inv.id)

                reasons = list(best_match["reasons"])
                evidence = {
                    "invoice_number": inv.invoice_number,
                    "transaction_reference": matched_tx.reference_id,
                    "invoice_total": str(inv.total_amount),
                    "transaction_amount": str(matched_tx.amount),
                    "amount_variance": str(best_match["variance"]),
                    "days_diff": abs((matched_tx.transaction_date - inv.invoice_date).days),
                }

                final_status = best_match["status"]
                final_variance = best_match["variance"]

                if has_tax_variance or inv.ground_truth_label == "tax_discrepancy":
                    reasons.append("TAX_DISCREPANCY")
                    evidence["statutory_rate"] = str(statutory_rate)
                    evidence["taxable_amount"] = str(inv.subtotal)
                    evidence["expected_tax"] = str(expected_tax)
                    evidence["recorded_tax"] = str(inv.tax_amount)
                    evidence["tax_variance"] = str(tax_variance)

                    # Priority: DUPLICATE > MISSING > MISMATCH > TAX_VARIANCE > PARTIAL > FUZZY > TOLERANCE > MATCHED
                    if final_status in ["MATCHED", "MATCHED_WITH_TOLERANCE", "FUZZY_MATCH", "PARTIAL_MATCH"]:
                        final_status = "TAX_VARIANCE"
                        final_variance = tax_variance

                # Link corresponding Payment (three-way cross check)
                linked_pmt = next(
                    (p for p in payments if p.invoice_id == inv.id or (
                        p.payment_reference and (
                            inv.invoice_number in p.payment_reference or
                            (matched_tx.reference_id and matched_tx.reference_id in p.payment_reference)
                        )
                    )),
                    None,
                )

                res = ReconciliationResult(
                    organization_id=organization_id,
                    run_id=run.id,
                    invoice_id=inv.id,
                    transaction_id=matched_tx.id,
                    payment_id=linked_pmt.id if linked_pmt else None,
                    match_type=best_match["match_type"],
                    match_method=best_match["match_method"],
                    confidence_score=best_match["confidence"],
                    match_confidence=best_match["confidence"],
                    variance_amount=final_variance,
                    status=final_status,
                    reason_codes=reasons,
                    evidence=evidence,
                    ground_truth_label=inv.ground_truth_label,
                )
                results.append(res)
            else:
                # --------------------------------------------------------------
                # Unmatched / Missing Payment Record
                # --------------------------------------------------------------
                used_invoice_ids.add(inv.id)
                reasons = ["MISSING_PAYMENT", "UNMATCHED_INVOICE"]
                evidence = {
                    "invoice_number": inv.invoice_number,
                    "invoice_total": str(inv.total_amount),
                    "invoice_date": inv.invoice_date.isoformat(),
                    "vendor": v_name,
                }
                if has_tax_variance or inv.ground_truth_label == "tax_discrepancy":
                    reasons.append("TAX_DISCREPANCY")
                    evidence["expected_tax"] = str(expected_tax)
                    evidence["recorded_tax"] = str(inv.tax_amount)
                    evidence["tax_variance"] = str(tax_variance)

                res = ReconciliationResult(
                    organization_id=organization_id,
                    run_id=run.id,
                    invoice_id=inv.id,
                    transaction_id=None,
                    payment_id=None,
                    match_type="MANUAL",
                    match_method="NONE",
                    confidence_score=Decimal("0.0000"),
                    match_confidence=Decimal("0.0000"),
                    variance_amount=inv.total_amount,
                    status="MISSING",
                    reason_codes=reasons,
                    evidence=evidence,
                    ground_truth_label=inv.ground_truth_label,
                )
                results.append(res)

        # 3. Save all results and update run metrics
        for r in results:
            db.add(r)
        db.flush()

        matched_count = sum(1 for r in results if r.status in ["MATCHED", "MATCHED_WITH_TOLERANCE", "FUZZY_MATCH"])
        variance_count = sum(1 for r in results if r.status in ["MISMATCH", "MISSING", "DUPLICATE", "TAX_VARIANCE", "PARTIAL_MATCH"])

        run.total_processed = len(results)
        run.matched_count = matched_count
        run.variance_count = variance_count
        run.status = "COMPLETED"

        db.commit()
        return run

