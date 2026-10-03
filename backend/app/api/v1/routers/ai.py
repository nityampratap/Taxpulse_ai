"""AI router: explain-case, summary, ask."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Case
from app.services.ai import AIService

router = APIRouter(prefix="/ai", tags=["ai"])
_ai = AIService()


class ExplainRequest(BaseModel):
    case_id: str
    prompt: Optional[str] = "Explain this tax discrepancy case."


class AskRequest(BaseModel):
    case_id: Optional[str] = None
    question: str


@router.post("/explain-case")
def explain_case(body: ExplainRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(
        (Case.id == body.case_id) | (Case.case_number == body.case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = _ai.explain_case(db, case, body.prompt or "Explain this tax discrepancy case.")
    db.commit()
    return result


@router.post("/summary")
def ai_summary(db: Session = Depends(get_db)):
    from app.models.models import Organization, ReconciliationResult
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")
    total = db.query(ReconciliationResult).filter_by(organization_id=org.id).count()
    cases = db.query(Case).filter_by(organization_id=org.id).all()
    critical = sum(1 for c in cases if c.priority == "CRITICAL")
    high = sum(1 for c in cases if c.priority == "HIGH")

    context = {
        "total_results": total, "total_cases": len(cases),
        "critical": critical, "high": high,
        "open": sum(1 for c in cases if c.status == "OPEN"),
    }
    from app.services.ai import MockAIProvider
    provider = MockAIProvider()
    result = provider.generate("Summarize the reconciliation results.", context)
    result["summary"] = (
        f"Reconciliation processed {total} records. "
        f"{len(cases)} exceptions found: {critical} critical, {high} high-risk. "
        f"Review recommended for critical cases."
    )
    return result


@router.post("/ask")
def ai_ask(body: AskRequest, db: Session = Depends(get_db)):
    if body.case_id:
        case = db.query(Case).filter(
            (Case.id == body.case_id) | (Case.case_number == body.case_id)
        ).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        result = _ai.explain_case(db, case, body.question)
        db.commit()
        return result
    return {"answer": "Please specify a case_id for context-bound questions.", "provider": "SYSTEM"}
