"""Exceptions router: alias for cases with exception-oriented filtering."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Case, Organization, ReconciliationResult, Invoice, Vendor

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


@router.get("")
def list_exceptions(
    status: Optional[str] = None, risk: Optional[str] = None,
    issue_type: Optional[str] = None, vendor: Optional[str] = None,
    sort_by: str = "risk_score", sort_order: str = "desc",
    limit: int = 50, offset: int = 0,
    db: Session = Depends(get_db),
):
    org = db.query(Organization).first()
    if not org:
        return {"exceptions": [], "total": 0}
    q = db.query(Case).filter_by(organization_id=org.id)
    if status:
        q = q.filter_by(status=status)
    if risk:
        q = q.filter_by(priority=risk)
    total = q.count()
    order_col = getattr(Case, sort_by, Case.risk_score)
    if sort_order == "desc":
        q = q.order_by(order_col.desc())
    else:
        q = q.order_by(order_col.asc())
    cases = q.offset(offset).limit(limit).all()

    results = []
    for c in cases:
        r = db.query(ReconciliationResult).filter_by(id=c.reconciliation_result_id).first()
        inv = db.query(Invoice).filter_by(id=r.invoice_id).first() if r and r.invoice_id else None
        v = db.query(Vendor).filter_by(id=inv.vendor_id).first() if inv else None
        results.append({
            "id": c.id, "case_number": c.case_number, "status": c.status,
            "priority": c.priority, "risk_score": str(c.risk_score),
            "financial_exposure": str(c.financial_exposure), "tax_impact": str(c.tax_impact),
            "issue_type": r.status if r else None,
            "match_method": r.match_method if r else None,
            "vendor_name": v.name if v else None,
            "invoice_number": inv.invoice_number if inv else None,
            "invoice_date": str(inv.invoice_date) if inv else None,
            "created_at": str(c.created_at),
        })
    return {"exceptions": results, "total": total}


@router.get("/{exception_id}")
def get_exception(exception_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(
        (Case.id == exception_id) | (Case.case_number == exception_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Exception not found")
    r = db.query(ReconciliationResult).filter_by(id=case.reconciliation_result_id).first()
    inv = db.query(Invoice).filter_by(id=r.invoice_id).first() if r and r.invoice_id else None
    v = db.query(Vendor).filter_by(id=inv.vendor_id).first() if inv else None
    from app.models.models import Payment
    pay = db.query(Payment).filter_by(id=r.payment_id).first() if r and r.payment_id else None
    return {
        "id": case.id, "case_number": case.case_number, "status": case.status,
        "priority": case.priority, "risk_score": str(case.risk_score),
        "financial_exposure": str(case.financial_exposure), "tax_impact": str(case.tax_impact),
        "factor_breakdown": case.factor_breakdown,
        "reconciliation": {
            "match_type": r.match_type, "status": r.status,
            "variance_amount": str(r.variance_amount), "confidence": str(r.confidence_score),
            "reason_codes": r.reason_codes, "evidence": r.evidence,
        } if r else None,
        "invoice": {
            "number": inv.invoice_number, "date": str(inv.invoice_date),
            "subtotal": str(inv.subtotal), "tax_amount": str(inv.tax_amount),
            "total_amount": str(inv.total_amount), "currency": inv.currency,
        } if inv else None,
        "vendor": {"name": v.name, "risk_tier": v.risk_tier} if v else None,
        "payment": {
            "reference": pay.payment_reference, "date": str(pay.payment_date),
            "amount": str(pay.amount_paid), "method": pay.payment_method,
        } if pay else None,
    }
