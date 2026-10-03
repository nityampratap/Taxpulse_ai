"""Append-only audit event service with SHA-256 tamper-evident hashing."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import AuditEvent


def _compute_hash(event_type: str, actor_id: str, entity_type: str,
                  entity_id: str, before_state: Any, after_state: Any,
                  timestamp: str) -> str:
    payload = json.dumps({
        "event_type": event_type,
        "actor_id": actor_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "before_state": before_state,
        "after_state": after_state,
        "timestamp": timestamp,
    }, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditService:
    """Records immutable audit events on every state transition."""

    @staticmethod
    def log(
        db: Session,
        *,
        organization_id: str,
        event_type: str,
        actor_id: str,
        entity_type: str,
        entity_id: str,
        after_state: Dict[str, Any],
        before_state: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        now = datetime.now(timezone.utc)
        ts_str = now.isoformat()
        checksum = _compute_hash(
            event_type, actor_id, entity_type, entity_id,
            before_state, after_state, ts_str,
        )
        event = AuditEvent(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            event_type=event_type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
            hash_checksum=checksum,
            timestamp=now,
        )
        db.add(event)
        return event

    @staticmethod
    def list_events(
        db: Session,
        organization_id: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        q = db.query(AuditEvent).filter_by(organization_id=organization_id)
        if entity_type:
            q = q.filter_by(entity_type=entity_type)
        if entity_id:
            q = q.filter_by(entity_id=entity_id)
        if event_type:
            q = q.filter_by(event_type=event_type)
        return q.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_event(db: Session, event_id: str) -> Optional[AuditEvent]:
        return db.query(AuditEvent).filter_by(id=event_id).first()
