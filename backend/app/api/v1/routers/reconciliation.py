"""Reconciliation router: run engine, list runs, get results."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import ReconciliationRun, ReconciliationResult, Organization
from app.services.reconciliation.engine import ReconciliationEngine
from app.services.anomaly import AnomalyDetector
from app.services.cases import CaseService
from app.services.audit import AuditService

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


class RunRequest(BaseModel):
    organization_id: Optional[str] = None
    batch_id: Optional[str] = None


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
def trigger_reconciliation(body: RunRequest, db: Session = Depends(get_db)):
    org_id = body.organization_id
    if not org_id:
        org = db.query(Organization).first()
        if not org:
            raise HTTPException(status_code=404, detail="No organization found. Generate demo data first.")
        org_id = org.id

    engine = ReconciliationEngine()
    run = engine.run(db, org_id, body.batch_id)

    # Run anomaly detection on results
    results = db.query(ReconciliationResult).filter_by(run_id=run.id).all()
    detector = AnomalyDetector()
    detector.detect(db, org_id, results)

    # Create cases from exception results
    case_svc = CaseService()
    cases = case_svc.create_cases_from_results(db, org_id, results)

    AuditService.log(
        db, organization_id=org_id, event_type="RECONCILIATION_RUN",
        actor_id="SYSTEM", entity_type="reconciliation_run", entity_id=run.id,
        after_state={"status": run.status, "total": run.total_processed,
                     "matched": run.matched_count, "variance": run.variance_count,
                     "cases_created": len(cases)},
    )
    db.commit()

    return {
        "run_id": run.id,
        "status": run.status,
        "total_processed": run.total_processed,
        "matched_count": run.matched_count,
        "variance_count": run.variance_count,
        "cases_created": len(cases),
    }


@router.get("/runs")
def list_reconciliation_runs(db: Session = Depends(get_db)):
    runs = db.query(ReconciliationRun).order_by(ReconciliationRun.run_timestamp.desc()).limit(50).all()
    return [
        {
            "id": r.id, "status": r.status, "total_processed": r.total_processed,
            "matched_count": r.matched_count, "variance_count": r.variance_count,
            "run_timestamp": str(r.run_timestamp), "batch_id": r.batch_id,
        }
        for r in runs
    ]


@router.get("/results/{result_id}")
def get_reconciliation_result(result_id: str, db: Session = Depends(get_db)):
    r = db.query(ReconciliationResult).filter_by(id=result_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Result not found")
    return {
        "id": r.id, "run_id": r.run_id, "invoice_id": r.invoice_id,
        "transaction_id": r.transaction_id, "payment_id": r.payment_id,
        "match_type": r.match_type, "match_method": r.match_method,
        "confidence_score": str(r.confidence_score),
        "match_confidence": str(r.match_confidence) if r.match_confidence else None,
        "variance_amount": str(r.variance_amount), "status": r.status,
        "reason_codes": r.reason_codes, "evidence": r.evidence,
    }
