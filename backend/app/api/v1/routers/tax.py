"""Tax router: rules CRUD, summary, exposure."""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Organization, TaxRule
from app.services.tax import TaxRateService, TaxEngine

router = APIRouter(prefix="/tax", tags=["tax"])


class TaxRuleCreate(BaseModel):
    tax_type: str = "GST"
    jurisdiction: str = "IN-MH"
    rate: str  # Decimal as string
    effective_from: str  # ISO date
    effective_to: Optional[str] = None


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return []
    rules = TaxRateService.list_rules(db, org.id)
    return [
        {
            "id": r.id, "tax_type": r.tax_type, "jurisdiction": r.jurisdiction,
            "rate": str(r.rate), "effective_from": str(r.effective_from),
            "effective_to": str(r.effective_to) if r.effective_to else None,
            "is_active": r.is_active,
        }
        for r in rules
    ]


@router.post("/rules", status_code=201)
def create_rule(body: TaxRuleCreate, db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")
    from app.services.audit import AuditService
    import uuid
    rule = TaxRule(
        id=str(uuid.uuid4()), organization_id=org.id,
        tax_type=body.tax_type, jurisdiction=body.jurisdiction,
        rate=Decimal(body.rate),
        effective_from=date.fromisoformat(body.effective_from),
        effective_to=date.fromisoformat(body.effective_to) if body.effective_to else None,
    )
    db.add(rule)
    AuditService.log(db, organization_id=org.id, event_type="TAX_RULE_CHANGED",
                     actor_id="SYSTEM", entity_type="tax_rule", entity_id=rule.id,
                     after_state={"rate": body.rate, "jurisdiction": body.jurisdiction})
    db.commit()
    return {"id": rule.id, "rate": str(rule.rate)}


@router.get("/summary")
def tax_summary(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return {"disclaimer": "Estimated from configured rates; not tax advice."}
    return TaxEngine.compute_summary(db, org.id)


@router.get("/exposure")
def tax_exposure(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return {"total_exposure": "0.00"}
    summary = TaxEngine.compute_summary(db, org.id)
    return {
        "total_exposure": str(summary["total_exposure"]),
        "variance_count": summary["variance_count"],
        "disclaimer": summary["disclaimer"],
    }
