"""Audit router: list events, get event detail."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Organization
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events")
def list_events(
    entity_type: Optional[str] = None, entity_id: Optional[str] = None,
    event_type: Optional[str] = None, limit: int = 100, offset: int = 0,
    db: Session = Depends(get_db),
):
    org = db.query(Organization).first()
    if not org:
        return []
    events = AuditService.list_events(db, org.id, entity_type, entity_id, event_type, limit, offset)
    return [
        {
            "id": e.id, "event_type": e.event_type, "actor_id": e.actor_id,
            "entity_type": e.entity_type, "entity_id": e.entity_id,
            "before_state": e.before_state, "after_state": e.after_state,
            "hash_checksum": e.hash_checksum, "timestamp": str(e.timestamp),
        }
        for e in events
    ]


@router.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = AuditService.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return {
        "id": event.id, "event_type": event.event_type, "actor_id": event.actor_id,
        "entity_type": event.entity_type, "entity_id": event.entity_id,
        "before_state": event.before_state, "after_state": event.after_state,
        "hash_checksum": event.hash_checksum, "timestamp": str(event.timestamp),
    }
