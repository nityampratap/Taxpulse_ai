"""Risk scoring engine: 6 weighted factors, boundary classification."""
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import ReconciliationResult, Invoice, Anomaly, Vendor, Case

# Default factor weights (configurable)
FACTORS = {
    "mismatch_severity": {"weight": 25, "description": "Severity of data mismatch"},
    "financial_exposure": {"weight": 25, "description": "Financial amount at risk"},
    "tax_impact": {"weight": 20, "description": "Tax variance impact"},
    "anomaly_score": {"weight": 15, "description": "Anomaly detection score"},
    "vendor_history": {"weight": 10, "description": "Vendor dispute history"},
    "recurrence": {"weight": 5, "description": "Pattern recurrence"},
}

# Risk levels (configurable boundaries)
RISK_LEVELS = [
    (75, "CRITICAL"),
    (55, "HIGH"),
    (30, "MEDIUM"),
    (0, "LOW"),
]


def classify_risk(score: float) -> str:
    for threshold, level in RISK_LEVELS:
        if score >= threshold:
            return level
    return "LOW"


class RiskScorer:
    """Computes composite risk score from 6 stored factors."""

    def score(
        self,
        db: Session,
        result: ReconciliationResult,
        anomaly: Optional[Anomaly] = None,
    ) -> Dict[str, Any]:
        invoice = db.query(Invoice).filter_by(id=result.invoice_id).first() if result.invoice_id else None
        vendor = None
        if invoice:
            vendor = db.query(Vendor).filter_by(id=invoice.vendor_id).first()

        factors: List[Dict[str, Any]] = []

        # 1. Mismatch severity (0-25)
        mismatch_pts = self._score_mismatch(result)
        factors.append({
            "factor": "mismatch_severity", "points": mismatch_pts, "max": 25,
            "explanation": self._explain_mismatch(result, mismatch_pts),
        })

        # 2. Financial exposure (0-25)
        exposure_pts = self._score_exposure(invoice)
        factors.append({
            "factor": "financial_exposure", "points": exposure_pts, "max": 25,
            "explanation": self._explain_exposure(invoice, exposure_pts),
        })

        # 3. Tax impact (0-20)
        tax_pts = self._score_tax(result)
        factors.append({
            "factor": "tax_impact", "points": tax_pts, "max": 20,
            "explanation": self._explain_tax(result, tax_pts),
        })

        # 4. Anomaly score (0-15)
        anomaly_pts = self._score_anomaly(anomaly)
        factors.append({
            "factor": "anomaly_score", "points": anomaly_pts, "max": 15,
            "explanation": f"Anomaly severity: {anomaly.severity_score if anomaly else 0}",
        })

        # 5. Vendor history (0-10)
        vendor_pts = self._score_vendor(vendor)
        factors.append({
            "factor": "vendor_history", "points": vendor_pts, "max": 10,
            "explanation": f"Vendor disputes: {vendor.dispute_count if vendor else 0}",
        })

        # 6. Recurrence (0-5)
        recurrence_pts = self._score_recurrence(db, result, invoice)
        factors.append({
            "factor": "recurrence", "points": recurrence_pts, "max": 5,
            "explanation": f"Similar pattern recurrence score",
        })

        total = sum(f["points"] for f in factors)
        total = min(100.0, max(0.0, total))
        level = classify_risk(total)

        return {
            "risk_score": Decimal(str(round(total, 2))),
            "risk_level": level,
            "risk_factors": factors,
        }

    def _score_mismatch(self, r: ReconciliationResult) -> float:
        status_scores = {
            "MATCHED": 0, "MATCHED_WITH_TOLERANCE": 3, "FUZZY_MATCH": 8,
            "PARTIAL_MATCH": 12, "MISMATCH": 20, "MISSING": 22,
            "DUPLICATE": 18, "TAX_VARIANCE": 15, "ANOMALY": 17,
        }
        return float(status_scores.get(r.status, 10))

    def _explain_mismatch(self, r: ReconciliationResult, pts: float) -> str:
        return f"Status {r.status}: {pts:.0f}/25 severity points"

    def _score_exposure(self, inv: Optional[Invoice]) -> float:
        if not inv:
            return 5.0
        amt = float(inv.total_amount)
        if amt >= 500000:
            return 25.0
        if amt > 100000:
            return 20.0
        if amt >= 50000:
            return 15.0
        if amt >= 10000:
            return 10.0
        return 5.0

    def _explain_exposure(self, inv: Optional[Invoice], pts: float) -> str:
        amt = inv.total_amount if inv else Decimal("0")
        return f"Exposure amount {amt}: {pts:.0f}/25 points"

    def _score_tax(self, r: ReconciliationResult) -> float:
        variance = abs(float(r.variance_amount))
        if variance >= 10000:
            return 20.0
        if variance >= 1000:
            return 15.0
        if variance >= 100:
            return 10.0
        if variance > 1:
            return 5.0
        return 0.0

    def _explain_tax(self, r: ReconciliationResult, pts: float) -> str:
        return f"Tax variance {r.variance_amount}: {pts:.0f}/20 points"

    def _score_anomaly(self, anomaly: Optional[Anomaly]) -> float:
        if not anomaly:
            return 0.0
        if anomaly.anomaly_type in ("TAX_DEVIATION", "STATISTICAL_OUTLIER") or float(anomaly.severity_score) >= 50:
            return 12.0
        score = float(anomaly.severity_score)
        return min(15.0, score * 0.15)

    def _score_vendor(self, vendor: Optional[Vendor]) -> float:
        if not vendor:
            return 0.0
        disputes = vendor.dispute_count
        if disputes >= 5:
            return 10.0
        if disputes >= 3:
            return 7.0
        if disputes >= 1:
            return 5.0
        return 0.0

    def _score_recurrence(self, db: Session, r: ReconciliationResult, inv: Optional[Invoice]) -> float:
        if not inv:
            return 0.0
        similar = (
            db.query(ReconciliationResult)
            .filter_by(organization_id=r.organization_id, status=r.status)
            .filter(ReconciliationResult.id != r.id)
            .limit(5)
            .count()
        )
        if similar >= 1:
            return 5.0
        return 0.0
