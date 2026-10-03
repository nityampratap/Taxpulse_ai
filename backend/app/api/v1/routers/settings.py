"""Settings router: tolerances, thresholds, integration status."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import os

from app.db.session import get_db
from app.config import settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings():
    return {
        "tolerances": {
            "amount_inr": str(settings.TOLERANCE_AMOUNT_INR),
            "amount_percent": str(settings.TOLERANCE_AMOUNT_PERCENT),
            "date_days": settings.TOLERANCE_DATE_DAYS,
        },
        "integrations": {
            "ai": {
                "provider_order": settings.AI_PROVIDER_ORDER,
                "groq": "configured" if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "UPDATE_ME" else "not configured",
                "gemini": "configured" if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "UPDATE_ME" else "not configured",
                "mock": "always available",
                "embedder": settings.EMBEDDER,
            },
            "whatsapp": {
                "mode": settings.WHATSAPP_MODE,
                "configured": bool(settings.WHATSAPP_VERIFY_TOKEN and settings.WHATSAPP_VERIFY_TOKEN != "UPDATE_ME"),
            },
            "storage": {
                "provider": settings.STORAGE_PROVIDER,
                "supabase": "configured" if settings.SUPABASE_URL and settings.SUPABASE_URL != "UPDATE_ME" else "not configured",
            },
            "database": {
                "type": "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite",
            },
        },
    }


class UpdateSettings(BaseModel):
    tolerance_amount_inr: Optional[str] = None
    tolerance_amount_percent: Optional[str] = None
    tolerance_date_days: Optional[int] = None


@router.put("")
def update_settings(body: UpdateSettings, db: Session = Depends(get_db)):
    from app.services.audit import AuditService
    from app.models.models import Organization
    from decimal import Decimal
    changes = {}
    if body.tolerance_amount_inr is not None:
        settings.TOLERANCE_AMOUNT_INR = Decimal(body.tolerance_amount_inr)
        changes["tolerance_amount_inr"] = body.tolerance_amount_inr
    if body.tolerance_amount_percent is not None:
        settings.TOLERANCE_AMOUNT_PERCENT = Decimal(body.tolerance_amount_percent)
        changes["tolerance_amount_percent"] = body.tolerance_amount_percent
    if body.tolerance_date_days is not None:
        settings.TOLERANCE_DATE_DAYS = body.tolerance_date_days
        changes["tolerance_date_days"] = body.tolerance_date_days

    org = db.query(Organization).first()
    if org and changes:
        AuditService.log(db, organization_id=org.id, event_type="SETTINGS_CHANGED",
                         actor_id="SYSTEM", entity_type="settings", entity_id="global",
                         after_state=changes)
        db.commit()
    return {"status": "updated", "changes": changes}
