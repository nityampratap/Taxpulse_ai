"""Dashboard router: real-time metrics and chart data from queries."""
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import (
    Organization, Case, ReconciliationResult, ReconciliationRun,
    Invoice, Anomaly,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return {"invoices_count": 0, "runs_count": 0, "total_transactions": 0, "matched": 0, "unmatched": 0,
                "duplicates": 0, "missing": 0, "tax_variance": "0.00",
                "potential_exposure": "0.00", "critical": 0, "high_risk": 0, "anomalies": 0}

    oid = org.id
    invoices_count = db.query(Invoice).filter_by(organization_id=oid).count()
    runs_count = db.query(ReconciliationRun).filter_by(organization_id=oid).count()
    total = db.query(ReconciliationResult).filter_by(organization_id=oid).count()
    matched = db.query(ReconciliationResult).filter_by(organization_id=oid).filter(
        ReconciliationResult.status.in_(["MATCHED", "MATCHED_WITH_TOLERANCE"])).count()
    unmatched = db.query(ReconciliationResult).filter_by(organization_id=oid).filter(
        ReconciliationResult.status.in_(["MISMATCH", "MISSING", "PARTIAL_MATCH"])).count()
    duplicates = db.query(ReconciliationResult).filter_by(organization_id=oid, status="DUPLICATE").count()
    missing = db.query(ReconciliationResult).filter_by(organization_id=oid, status="MISSING").count()

    variance_sum = db.query(func.sum(func.abs(ReconciliationResult.variance_amount))).filter_by(
        organization_id=oid).filter(ReconciliationResult.status == "TAX_VARIANCE").scalar() or Decimal("0")
    exposure_sum = db.query(func.sum(Case.financial_exposure)).filter_by(organization_id=oid).scalar() or Decimal("0")
    critical = db.query(Case).filter_by(organization_id=oid, priority="CRITICAL").count()
    high_risk = db.query(Case).filter_by(organization_id=oid, priority="HIGH").count()
    anomalies = db.query(Anomaly).filter_by(organization_id=oid).count()

    return {
        "invoices_count": invoices_count, "runs_count": runs_count,
        "total_transactions": total, "matched": matched, "unmatched": unmatched,
        "duplicates": duplicates, "missing": missing,
        "tax_variance": str(variance_sum), "potential_exposure": str(exposure_sum),
        "critical": critical, "high_risk": high_risk, "anomalies": anomalies,
    }


@router.get("/charts")
def get_charts(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return {"status_distribution": [], "risk_distribution": [], "vendor_exposure": [],
                "tax_variance": [], "anomaly_trend": []}
    oid = org.id

    # Status distribution
    status_dist = db.query(
        ReconciliationResult.status, func.count(ReconciliationResult.id)
    ).filter_by(organization_id=oid).group_by(ReconciliationResult.status).all()

    # Risk distribution
    risk_dist = db.query(
        Case.priority, func.count(Case.id)
    ).filter_by(organization_id=oid).group_by(Case.priority).all()

    # Vendor exposure (top 10)
    from app.models.models import Vendor
    vendor_exp = (
        db.query(Vendor.name, func.sum(Case.financial_exposure))
        .join(Invoice, Invoice.vendor_id == Vendor.id)
        .join(ReconciliationResult, ReconciliationResult.invoice_id == Invoice.id)
        .join(Case, Case.reconciliation_result_id == ReconciliationResult.id)
        .filter(Case.organization_id == oid)
        .group_by(Vendor.name)
        .order_by(func.sum(Case.financial_exposure).desc())
        .limit(10)
        .all()
    )

    # Tax variance by status
    tax_var = db.query(
        ReconciliationResult.status,
        func.sum(func.abs(ReconciliationResult.variance_amount))
    ).filter_by(organization_id=oid).filter(
        ReconciliationResult.variance_amount != 0
    ).group_by(ReconciliationResult.status).all()

    return {
        "status_distribution": [{"status": s, "count": c} for s, c in status_dist],
        "risk_distribution": [{"level": l, "count": c} for l, c in risk_dist],
        "vendor_exposure": [{"vendor": n, "exposure": str(e)} for n, e in vendor_exp],
        "tax_variance": [{"status": s, "variance": str(v)} for s, v in tax_var],
        "anomaly_trend": [],
    }


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return get_metrics(db=db)
