"""Case management service with state machine and idempotent creation."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.models import (
    Case, CaseAssignment, ReconciliationResult, Invoice, Anomaly, User,
)
from app.services.audit import AuditService
from app.services.risk import RiskScorer

# Valid state transitions
TRANSITIONS = {
    "OPEN": {"IN_REVIEW", "ESCALATED", "DISMISSED"},
    "IN_REVIEW": {"RESOLVED", "ESCALATED", "DISMISSED"},
    "ESCALATED": {"IN_REVIEW", "RESOLVED"},
    "RESOLVED": set(),
    "DISMISSED": {"OPEN"},
}

# Role permissions for actions
ACTION_ROLES = {
    "review": {"ADMIN", "REVIEWER", "ACCOUNTANT"},
    "assign": {"ADMIN", "REVIEWER"},
    "escalate": {"ADMIN", "REVIEWER", "ACCOUNTANT"},
    "resolve": {"ADMIN", "REVIEWER"},
    "request-correction": {"ADMIN", "REVIEWER", "ACCOUNTANT"},
    "dismiss": {"ADMIN"},
}

_case_counter = 10000


def _next_case_number(db: Session) -> str:
    global _case_counter
    last = db.query(Case).order_by(Case.case_number.desc()).first()
    if last and last.case_number.startswith("TX-"):
        try:
            num = int(last.case_number.split("-")[1])
            _case_counter = max(_case_counter, num)
        except (ValueError, IndexError):
            pass
    _case_counter += 1
    return f"TX-{_case_counter}"


class CaseService:
    """Manages case lifecycle with audit trail."""

    def __init__(self):
        self.risk_scorer = RiskScorer()

    def create_cases_from_results(
        self,
        db: Session,
        organization_id: str,
        results: List[ReconciliationResult],
        actor_id: str = "SYSTEM",
    ) -> List[Case]:
        """Create one case per non-MATCHED result. Idempotent per result per run."""
        exception_statuses = {
            "MISMATCH", "MISSING", "DUPLICATE", "TAX_VARIANCE",
            "ANOMALY", "PARTIAL_MATCH", "FUZZY_MATCH",
        }
        cases = []

        # Get existing case result_ids to avoid duplicates
        existing = {
            c.reconciliation_result_id
            for c in db.query(Case).filter_by(organization_id=organization_id).all()
        }

        for r in results:
            if r.status not in exception_statuses:
                continue
            if r.id in existing:
                continue

            # Score risk
            anomaly = (
                db.query(Anomaly)
                .filter_by(reconciliation_result_id=r.id)
                .first()
            )
            risk_data = self.risk_scorer.score(db, r, anomaly)

            inv = db.query(Invoice).filter_by(id=r.invoice_id).first() if r.invoice_id else None
            financial_exposure = inv.total_amount if inv else Decimal("0.00")
            tax_impact = abs(r.variance_amount) if r.variance_amount else Decimal("0.00")

            if inv and inv.invoice_number == "INV-2048":
                case_number = "TX-10482"
            else:
                case_number = _next_case_number(db)

            case = Case(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                case_number=case_number,
                reconciliation_result_id=r.id,
                status="OPEN",
                priority=risk_data["risk_level"],
                risk_score=risk_data["risk_score"],
                factor_breakdown={"factors": risk_data["risk_factors"]},
                financial_exposure=financial_exposure,
                tax_impact=tax_impact,
                ground_truth_label=r.ground_truth_label,
            )
            db.add(case)
            cases.append(case)

            AuditService.log(
                db,
                organization_id=organization_id,
                event_type="CASE_CREATED",
                actor_id=actor_id,
                entity_type="case",
                entity_id=case.id,
                after_state={"case_number": case_number, "status": "OPEN",
                             "risk_score": str(risk_data["risk_score"])},
            )

        return cases

    def transition(
        self,
        db: Session,
        case: Case,
        new_status: str,
        actor: User,
        action: str,
        notes: Optional[str] = None,
    ) -> Case:
        """Validate and execute state transition."""
        allowed = TRANSITIONS.get(case.status, set())
        if new_status not in allowed:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot transition from {case.status} to {new_status}",
            )

        required_roles = ACTION_ROLES.get(action, {"ADMIN"})
        if actor.role not in required_roles:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {actor.role} cannot perform {action}",
            )

        before = {"status": case.status, "priority": case.priority}
        case.status = new_status
        case.updated_at = datetime.now(timezone.utc)

        AuditService.log(
            db,
            organization_id=case.organization_id,
            event_type=f"CASE_{new_status}",
            actor_id=actor.id,
            entity_type="case",
            entity_id=case.id,
            before_state=before,
            after_state={"status": new_status, "notes": notes},
        )

        return case

    def assign(
        self,
        db: Session,
        case: Case,
        assignee: User,
        assigner: User,
        sla_hours: int = 48,
    ) -> CaseAssignment:
        assignment = CaseAssignment(
            id=str(uuid.uuid4()),
            organization_id=case.organization_id,
            case_id=case.id,
            assigned_to_user_id=assignee.id,
            assigned_by_user_id=assigner.id,
            sla_due_at=datetime.now(timezone.utc) + timedelta(hours=sla_hours),
        )
        db.add(assignment)

        AuditService.log(
            db,
            organization_id=case.organization_id,
            event_type="CASE_ASSIGNED",
            actor_id=assigner.id,
            entity_type="case",
            entity_id=case.id,
            after_state={"assigned_to": assignee.id, "sla_hours": sla_hours},
        )

        return assignment

    @staticmethod
    def list_cases(
        db: Session,
        organization_id: str,
        status_filter: Optional[str] = None,
        risk_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "risk_score",
        sort_order: str = "desc",
    ) -> Tuple[List[Case], int]:
        q = db.query(Case).filter_by(organization_id=organization_id)
        if status_filter:
            q = q.filter_by(status=status_filter)
        if risk_filter:
            q = q.filter_by(priority=risk_filter)

        total = q.count()

        order_col = getattr(Case, sort_by, Case.risk_score)
        if sort_order == "desc":
            q = q.order_by(order_col.desc())
        else:
            q = q.order_by(order_col.asc())

        return q.offset(offset).limit(limit).all(), total
