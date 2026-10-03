"""Cases router: list, detail, state transitions with audit."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Case, User, Invoice, ReconciliationResult, Vendor
from app.services.cases import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])
_svc = CaseService()


class AssignRequest(BaseModel):
    assignee_user_id: str


class ActionRequest(BaseModel):
    notes: Optional[str] = None


def _case_detail(db: Session, case: Case) -> dict:
    result = db.query(ReconciliationResult).filter_by(id=case.reconciliation_result_id).first()
    invoice = db.query(Invoice).filter_by(id=result.invoice_id).first() if result and result.invoice_id else None
    vendor = db.query(Vendor).filter_by(id=invoice.vendor_id).first() if invoice else None
    return {
        "id": case.id, "case_number": case.case_number, "status": case.status,
        "priority": case.priority, "risk_score": str(case.risk_score),
        "financial_exposure": str(case.financial_exposure),
        "tax_impact": str(case.tax_impact),
        "factor_breakdown": case.factor_breakdown,
        "created_at": str(case.created_at), "updated_at": str(case.updated_at),
        "reconciliation_result": {
            "id": result.id, "match_type": result.match_type, "status": result.status,
            "variance_amount": str(result.variance_amount),
            "confidence_score": str(result.confidence_score),
            "reason_codes": result.reason_codes, "evidence": result.evidence,
        } if result else None,
        "invoice": {
            "id": invoice.id, "number": invoice.invoice_number,
            "date": str(invoice.invoice_date), "subtotal": str(invoice.subtotal),
            "tax_amount": str(invoice.tax_amount), "total_amount": str(invoice.total_amount),
        } if invoice else None,
        "vendor": {"id": vendor.id, "name": vendor.name, "risk_tier": vendor.risk_tier} if vendor else None,
    }


@router.get("")
def list_cases(
    status_filter: Optional[str] = None, risk: Optional[str] = None,
    sort_by: str = "risk_score", sort_order: str = "desc",
    limit: int = 50, offset: int = 0,
    db: Session = Depends(get_db),
):
    from app.models.models import Organization
    org = db.query(Organization).first()
    if not org:
        return {"cases": [], "total": 0}
    cases, total = _svc.list_cases(db, org.id, status_filter, risk, limit, offset, sort_by, sort_order)
    return {"cases": [_case_detail(db, c) for c in cases], "total": total}


@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(
        (Case.id == case_id) | (Case.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_detail(db, case)


def _get_system_user(db: Session) -> User:
    user = db.query(User).filter_by(role="ADMIN").first()
    if not user:
        user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=400, detail="No users found")
    return user


@router.post("/{case_id}/review")
def review_case(case_id: str, body: ActionRequest = None, db: Session = Depends(get_db)):
    case = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    user = _get_system_user(db)
    _svc.transition(db, case, "IN_REVIEW", user, "review", body.notes if body else None)
    db.commit()
    return _case_detail(db, case)


@router.post("/{case_id}/assign")
def assign_case(case_id: str, body: AssignRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    assigner = _get_system_user(db)
    assignee = db.query(User).filter_by(id=body.assignee_user_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    _svc.assign(db, case, assignee, assigner)
    db.commit()
    return _case_detail(db, case)


@router.post("/{case_id}/escalate")
def escalate_case(case_id: str, body: ActionRequest = None, db: Session = Depends(get_db)):
    case = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    user = _get_system_user(db)
    _svc.transition(db, case, "ESCALATED", user, "escalate", body.notes if body else None)
    db.commit()
    return _case_detail(db, case)


@router.post("/{case_id}/resolve")
def resolve_case(case_id: str, body: ActionRequest = None, db: Session = Depends(get_db)):
    case = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    user = _get_system_user(db)
    if case.status == "OPEN":
        _svc.transition(db, case, "IN_REVIEW", user, "review")
    _svc.transition(db, case, "RESOLVED", user, "resolve", body.notes if body else None)
    db.commit()
    return _case_detail(db, case)


@router.post("/{case_id}/request-correction")
def request_correction(case_id: str, body: ActionRequest = None, db: Session = Depends(get_db)):
    case = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    user = _get_system_user(db)
    from app.services.audit import AuditService
    AuditService.log(db, organization_id=case.organization_id, event_type="CORRECTION_REQUESTED",
                     actor_id=user.id, entity_type="case", entity_id=case.id,
                     after_state={"notes": body.notes if body else "Correction requested"})
    db.commit()
    return {"status": "correction_requested", "case": _case_detail(db, case)}


@router.post("/{case_id}/dismiss")
def dismiss_case(case_id: str, body: ActionRequest = None, db: Session = Depends(get_db)):
    case = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    user = _get_system_user(db)
    _svc.transition(db, case, "DISMISSED", user, "dismiss", body.notes if body else None)
    db.commit()
    return _case_detail(db, case)
