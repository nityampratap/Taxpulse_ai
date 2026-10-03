"""Tax engine: TaxRateService (temporal lookup) and TaxEngine (verify)."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.models.models import TaxRule


class TaxRateService:
    """Single source of truth for tax rate lookups."""

    @staticmethod
    def get_rate(
        db: Session,
        organization_id: str,
        tax_type: str = "GST",
        jurisdiction: str = "IN-MH",
        on_date: Optional[date] = None,
    ) -> Optional[TaxRule]:
        on_date = on_date or date.today()
        q = (
            db.query(TaxRule)
            .filter_by(organization_id=organization_id, tax_type=tax_type,
                       jurisdiction=jurisdiction, is_active=True)
            .filter(TaxRule.effective_from <= on_date)
            .filter((TaxRule.effective_to.is_(None)) | (TaxRule.effective_to >= on_date))
            .order_by(TaxRule.effective_from.desc())
        )
        return q.first()

    @staticmethod
    def list_rules(db: Session, organization_id: str) -> List[TaxRule]:
        return (
            db.query(TaxRule)
            .filter_by(organization_id=organization_id)
            .order_by(TaxRule.effective_from.desc())
            .all()
        )


class TaxEngine:
    """Verifies recorded tax against statutory rates. Never says 'compliant'."""

    ROUNDING = ROUND_HALF_UP
    TAX_TOLERANCE = Decimal("1.00")  # +-1 INR

    @staticmethod
    def verify(
        taxable_amount: Decimal,
        recorded_tax: Decimal,
        statutory_rate: Decimal,
        rounding: str = ROUND_HALF_UP,
    ) -> Dict[str, Any]:
        expected_tax = (taxable_amount * statutory_rate).quantize(Decimal("0.01"), rounding=rounding)
        variance = recorded_tax - expected_tax
        abs_variance = abs(variance)
        potential_liability = max(Decimal("0.00"), expected_tax - recorded_tax)
        potential_exposure = abs_variance

        has_variance = abs_variance > TaxEngine.TAX_TOLERANCE

        return {
            "taxable_amount": taxable_amount,
            "statutory_rate": statutory_rate,
            "expected_tax": expected_tax,
            "recorded_tax": recorded_tax,
            "variance": variance,
            "abs_variance": abs_variance,
            "potential_liability": potential_liability,
            "potential_exposure": potential_exposure,
            "has_variance": has_variance,
            "direction": "OVER" if variance > 0 else "UNDER" if variance < 0 else "EXACT",
        }

    @staticmethod
    def compute_summary(
        db: Session,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Compute tax summary across all invoices for an org."""
        from app.models.models import Invoice, Vendor
        invoices = db.query(Invoice).filter_by(organization_id=organization_id).all()
        rate_svc = TaxRateService()

        total_expected = Decimal("0.00")
        total_recorded = Decimal("0.00")
        total_variance = Decimal("0.00")
        total_exposure = Decimal("0.00")
        variance_count = 0

        for inv in invoices:
            rule = rate_svc.get_rate(db, organization_id, on_date=inv.invoice_date)
            if not rule:
                continue
            result = TaxEngine.verify(inv.subtotal, inv.tax_amount, rule.rate)
            total_expected += result["expected_tax"]
            total_recorded += result["recorded_tax"]
            total_variance += result["variance"]
            total_exposure += result["potential_exposure"]
            if result["has_variance"]:
                variance_count += 1

        return {
            "total_invoices": len(invoices),
            "total_expected_tax": total_expected,
            "total_recorded_tax": total_recorded,
            "total_variance": total_variance,
            "total_exposure": total_exposure,
            "variance_count": variance_count,
            "disclaimer": "Estimated from configured rates; not tax advice.",
        }
