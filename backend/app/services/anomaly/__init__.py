"""Anomaly detection: deterministic rule signals + IsolationForest."""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session

from app.models.models import Anomaly, ReconciliationResult, Invoice, Transaction, Payment

logger = logging.getLogger(__name__)

SIGNAL_LARGE_AMOUNT = "LARGE_AMOUNT"
SIGNAL_ROUND_VALUE = "ROUND_VALUE_REPEAT"
SIGNAL_VENDOR_SPIKE = "VENDOR_SPIKE"
SIGNAL_REPEATED_PATTERN = "REPEATED_PATTERN"
SIGNAL_TAX_DEVIATION = "TAX_DEVIATION"
SIGNAL_DUPLICATE_LIKE = "DUPLICATE_LIKE"
SIGNAL_UNUSUAL_TIMING = "UNUSUAL_TIMING"
SIGNAL_HIGH_FREQUENCY = "HIGH_FREQUENCY"
SIGNAL_ISOLATION_FOREST = "ISOLATION_FOREST"


def _robust_zscore(values: List[float], idx: int) -> float:
    """Robust z-score using median and MAD."""
    if len(values) < 3:
        return 0.0
    arr = np.array(values)
    med = np.median(arr)
    mad = np.median(np.abs(arr - med))
    if mad < 1e-10:
        return 0.0
    return float(abs(arr[idx] - med) / (mad * 1.4826))


class AnomalyDetector:
    """Detects anomalies using deterministic signals and IsolationForest."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def detect(
        self,
        db: Session,
        organization_id: str,
        results: List[ReconciliationResult],
    ) -> List[Anomaly]:
        if not results:
            return []

        invoices = {i.id: i for i in db.query(Invoice).filter_by(organization_id=organization_id).all()}
        transactions = {t.id: t for t in db.query(Transaction).filter_by(organization_id=organization_id).all()}

        amounts = []
        features_list = []
        result_signals: List[Dict[str, Any]] = []

        for r in results:
            inv = invoices.get(r.invoice_id) if r.invoice_id else None
            txn = transactions.get(r.transaction_id) if r.transaction_id else None
            amt = float(inv.total_amount) if inv else (float(txn.amount) if txn else 0.0)
            amounts.append(amt)

            signals: Dict[str, float] = {}
            reasons: List[str] = []

            # Tax deviation
            if r.status in ("TAX_VARIANCE", "MISMATCH") and r.evidence:
                ev = r.evidence if isinstance(r.evidence, dict) else {}
                if ev.get("tax_variance") or ev.get("variance_amount"):
                    signals[SIGNAL_TAX_DEVIATION] = 0.8
                    reasons.append(SIGNAL_TAX_DEVIATION)

            # Duplicate-like
            if r.status == "DUPLICATE":
                signals[SIGNAL_DUPLICATE_LIKE] = 0.9
                reasons.append(SIGNAL_DUPLICATE_LIKE)

            # Round value detection
            if amt > 0 and amt % 1000 == 0 and amt >= 10000:
                signals[SIGNAL_ROUND_VALUE] = 0.5
                reasons.append(SIGNAL_ROUND_VALUE)

            variance = float(r.variance_amount) if r.variance_amount else 0.0
            tax_ratio = 0.0
            if inv and float(inv.subtotal) > 0:
                tax_ratio = float(inv.tax_amount) / float(inv.subtotal)

            features_list.append([amt, abs(variance), tax_ratio])
            result_signals.append({"signals": signals, "reasons": reasons})

        # Large amount detection (robust z > 3.5)
        for i, amt in enumerate(amounts):
            z = _robust_zscore(amounts, i)
            if z > 3.5:
                result_signals[i]["signals"][SIGNAL_LARGE_AMOUNT] = min(1.0, z / 5.0)
                result_signals[i]["reasons"].append(SIGNAL_LARGE_AMOUNT)

        # Vendor spike detection (median + 3*MAD per vendor)
        vendor_counts: Dict[str, List[int]] = {}
        for i, r in enumerate(results):
            inv = invoices.get(r.invoice_id) if r.invoice_id else None
            vid = inv.vendor_id if inv else "unknown"
            vendor_counts.setdefault(vid, []).append(i)

        for vid, indices in vendor_counts.items():
            if len(indices) >= 3:
                vendor_amts = [amounts[j] for j in indices]
                med = float(np.median(vendor_amts))
                mad = float(np.median(np.abs(np.array(vendor_amts) - med)))
                threshold = med + 3 * max(mad, 1.0)
                for j in indices:
                    if amounts[j] > threshold:
                        result_signals[j]["signals"][SIGNAL_VENDOR_SPIKE] = 0.75
                        result_signals[j]["reasons"].append(SIGNAL_VENDOR_SPIKE)

        # IsolationForest (skip if < 30 rows)
        if_scores = [0.0] * len(results)
        if len(features_list) >= 30:
            try:
                from sklearn.ensemble import IsolationForest
                X = np.array(features_list)
                clf = IsolationForest(
                    n_estimators=100, contamination=0.1,
                    random_state=self.random_state,
                )
                clf.fit(X)
                raw_scores = clf.decision_function(X)
                # Normalize: more negative = more anomalous -> higher score
                min_s, max_s = raw_scores.min(), raw_scores.max()
                if max_s - min_s > 1e-10:
                    if_scores = [float(1.0 - (s - min_s) / (max_s - min_s)) for s in raw_scores]
                else:
                    if_scores = [0.5] * len(raw_scores)
            except Exception as e:
                logger.warning("IsolationForest skipped: %s", e)
        else:
            logger.info("IsolationForest skipped: only %d rows (need >= 30)", len(features_list))

        # Build anomalies
        anomalies: List[Anomaly] = []
        for i, r in enumerate(results):
            sigs = result_signals[i]["signals"]
            reasons = result_signals[i]["reasons"]

            if if_scores[i] > 0.7:
                sigs[SIGNAL_ISOLATION_FOREST] = if_scores[i]
                reasons.append(SIGNAL_ISOLATION_FOREST)

            if not sigs:
                continue

            max_rule_strength = max(sigs.values()) if sigs else 0.0
            anomaly_score = max(if_scores[i], 0.7 * max_rule_strength)

            detector = "RULE_ENGINE"
            if SIGNAL_ISOLATION_FOREST in sigs:
                detector = "ISOLATION_FOREST"

            anomaly_type = reasons[0] if reasons else "STATISTICAL_OUTLIER"

            anomaly = Anomaly(
                id=str(uuid.uuid4()),
                organization_id=r.organization_id,
                reconciliation_result_id=r.id,
                anomaly_type=anomaly_type,
                detector_type=detector,
                severity_score=Decimal(str(round(anomaly_score * 100, 2))),
                raw_features={
                    "signals": sigs,
                    "reasons": reasons,
                    "amount": amounts[i],
                    "if_score": if_scores[i],
                    "anomaly_score": anomaly_score,
                },
            )
            anomalies.append(anomaly)
            db.add(anomaly)

        db.flush()
        return anomalies
