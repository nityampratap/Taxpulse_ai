"""Reports router: CSV/XLSX export for reconciliation, exceptions, tax, audit."""
import csv
import io
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import (
    Organization, ReconciliationResult, Case, Invoice, Vendor,
    AuditEvent,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _escape_csv_cell(val: str) -> str:
    """Prevent CSV formula injection."""
    if val and val[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + val
    return val


def _generate_csv(headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_escape_csv_cell(str(v)) for v in row])
    output.seek(0)
    return output


@router.get("/reconciliation.csv")
def reconciliation_csv(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No data")
    results = db.query(ReconciliationResult).filter_by(organization_id=org.id).all()
    headers = ["ID", "Status", "Match Type", "Confidence", "Variance", "Invoice ID", "Transaction ID"]
    rows = [[r.id, r.status, r.match_type, str(r.confidence_score), str(r.variance_amount),
             r.invoice_id or "", r.transaction_id or ""] for r in results]
    output = _generate_csv(headers, rows)
    return StreamingResponse(output, media_type="text/csv",
                            headers={"Content-Disposition": "attachment; filename=reconciliation.csv"})


@router.get("/exceptions.csv")
def exceptions_csv(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No data")
    cases = db.query(Case).filter_by(organization_id=org.id).all()
    headers = ["Case Number", "Status", "Priority", "Risk Score", "Financial Exposure", "Tax Impact"]
    rows = [[c.case_number, c.status, c.priority, str(c.risk_score),
             str(c.financial_exposure), str(c.tax_impact)] for c in cases]
    output = _generate_csv(headers, rows)
    return StreamingResponse(output, media_type="text/csv",
                            headers={"Content-Disposition": "attachment; filename=exceptions.csv"})


@router.get("/tax-exposure.csv")
def tax_exposure_csv(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No data")
    from app.services.tax import TaxEngine
    summary = TaxEngine.compute_summary(db, org.id)
    headers = ["Metric", "Value"]
    rows = [[k, str(v)] for k, v in summary.items()]
    output = _generate_csv(headers, rows)
    return StreamingResponse(output, media_type="text/csv",
                            headers={"Content-Disposition": "attachment; filename=tax-exposure.csv"})


@router.get("/audit.csv")
def audit_csv(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No data")
    events = db.query(AuditEvent).filter_by(organization_id=org.id).order_by(
        AuditEvent.timestamp.desc()).limit(1000).all()
    headers = ["Timestamp", "Event Type", "Actor", "Entity Type", "Entity ID", "Hash"]
    rows = [[str(e.timestamp), e.event_type, e.actor_id, e.entity_type, e.entity_id,
             e.hash_checksum] for e in events]
    output = _generate_csv(headers, rows)
    return StreamingResponse(output, media_type="text/csv",
                            headers={"Content-Disposition": "attachment; filename=audit.csv"})
