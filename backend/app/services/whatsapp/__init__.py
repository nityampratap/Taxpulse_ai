"""WhatsApp service: MockProvider + CommandRouter + pending confirmations."""
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import (
    WhatsAppMessage, PendingConfirmation, Case, User,
)
from app.services.audit import AuditService
from app.services.cases import CaseService

logger = logging.getLogger(__name__)

CONFIRMATION_EXPIRY_MINUTES = 10


class BaseWhatsAppProvider(ABC):
    @abstractmethod
    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class MockWhatsAppProvider(BaseWhatsAppProvider):
    """Demo mode: stores messages in DB, no external calls."""
    name = "MOCK"

    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        return {"status": "sent", "provider": "MOCK", "phone": phone}


class CloudAPIProvider(BaseWhatsAppProvider):
    """Meta WhatsApp Cloud API provider."""
    name = "CLOUD_API"

    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        import httpx
        access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
        phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        api_version = os.environ.get("WHATSAPP_API_VERSION", "v17.0")

        if not access_token or not phone_id:
            raise ValueError("WhatsApp Cloud API credentials not configured")

        resp = httpx.post(
            f"https://graph.facebook.com/{api_version}/{phone_id}/messages",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp", "to": phone, "type": "text",
                  "text": {"body": message}},
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"status": "sent", "provider": "CLOUD_API", "response": resp.json()}


def _get_provider() -> BaseWhatsAppProvider:
    mode = os.environ.get("WHATSAPP_MODE", "DEMO").upper()
    if mode == "LIVE":
        try:
            return CloudAPIProvider()
        except Exception:
            pass
    return MockWhatsAppProvider()


class WhatsAppService:
    """Manages WhatsApp messaging with command routing."""

    def __init__(self):
        self.provider = _get_provider()
        self.case_service = CaseService()

    def send_alert(
        self,
        db: Session,
        case: Case,
        phone: str,
        organization_id: str,
    ) -> WhatsAppMessage:
        message_body = (
            f"⚠️ TAXPULSE ALERT\n"
            f"Critical tax discrepancy\n"
            f"Case: {case.case_number}\n"
            f"Risk: {case.priority}\n"
            f"Financial exposure: {case.financial_exposure}\n"
            f"Tax variance: {case.tax_impact}\n"
            f"Reply: EXPLAIN {case.case_number}"
        )
        self.provider.send_message(phone, message_body)

        msg = WhatsAppMessage(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            case_id=case.id,
            recipient_phone=phone,
            direction="OUTBOUND",
            message_body=message_body,
            status="SENT",
        )
        db.add(msg)

        AuditService.log(
            db,
            organization_id=organization_id,
            event_type="WHATSAPP_ALERT_SENT",
            actor_id="SYSTEM",
            entity_type="case",
            entity_id=case.id,
            after_state={"phone": phone[:6] + "****", "case": case.case_number},
        )

        return msg

    def handle_inbound(
        self,
        db: Session,
        phone: str,
        text: str,
        organization_id: str,
    ) -> str:
        """Process inbound message and return response text."""
        text = text.strip().upper()
        parts = text.split()
        command = parts[0] if parts else ""

        # Record inbound message
        inbound = WhatsAppMessage(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            recipient_phone=phone,
            direction="INBOUND",
            message_body=text,
            status="RECEIVED",
        )
        db.add(inbound)

        if command == "HELP":
            return self._reply(db, phone, organization_id, None,
                "TAXPULSE Commands:\n"
                "SUMMARY - Dashboard summary\n"
                "CRITICAL - List critical cases\n"
                "EXPLAIN <id> - Explain a case\n"
                "CASE <id> - Case details\n"
                "REVIEW <id> - Start review\n"
                "CONFIRM <id> - Confirm pending action\n"
                "CANCEL - Cancel pending action")

        if command == "SUMMARY":
            count = db.query(Case).filter_by(organization_id=organization_id).count()
            open_count = db.query(Case).filter_by(organization_id=organization_id, status="OPEN").count()
            critical = db.query(Case).filter_by(organization_id=organization_id, priority="CRITICAL").count()
            return self._reply(db, phone, organization_id, None,
                f"📊 TAXPULSE Summary\nTotal cases: {count}\nOpen: {open_count}\nCritical: {critical}")

        if command == "CRITICAL":
            cases = db.query(Case).filter_by(
                organization_id=organization_id, priority="CRITICAL"
            ).limit(5).all()
            if not cases:
                return self._reply(db, phone, organization_id, None, "No critical cases.")
            lines = [f"• {c.case_number} - {c.status} - Exposure: {c.financial_exposure}" for c in cases]
            return self._reply(db, phone, organization_id, None,
                "🚨 Critical Cases:\n" + "\n".join(lines))

        if command in ("EXPLAIN", "CASE") and len(parts) >= 2:
            case_num = parts[1]
            case = db.query(Case).filter_by(
                organization_id=organization_id, case_number=case_num
            ).first()
            if not case:
                return self._reply(db, phone, organization_id, None, f"Case {case_num} not found.")

            if command == "EXPLAIN":
                from app.services.ai import AIService
                ai = AIService()
                result = ai.explain_case(db, case, actor_id="WHATSAPP")
                return self._reply(db, phone, organization_id, case.id,
                    f"📋 TAXPULSE AI ANALYSIS ({case.case_number}):\n{result.get('summary', 'N/A')}")

            return self._reply(db, phone, organization_id, case.id,
                f"Case {case.case_number}\n"
                f"Status: {case.status}\nRisk: {case.priority} ({case.risk_score})\n"
                f"Exposure: {case.financial_exposure}\nTax impact: {case.tax_impact}")

        if command == "REVIEW" and len(parts) >= 2:
            case_num = parts[1]
            case = db.query(Case).filter_by(
                organization_id=organization_id, case_number=case_num
            ).first()
            if not case:
                return self._reply(db, phone, organization_id, None, f"Case {case_num} not found.")

            # Create pending confirmation
            code = case.case_number
            conf = PendingConfirmation(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                case_id=case.id,
                confirmation_code=f"CONFIRM {code}",
                action_payload={"action": "review", "target_status": "IN_REVIEW"},
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=CONFIRMATION_EXPIRY_MINUTES),
            )
            db.add(conf)
            db.flush()
            return self._reply(db, phone, organization_id, case.id,
                f"🔒 PENDING CONFIRMATION:\n"
                f"This will review case {case.case_number}.\n"
                f"Reply CONFIRM {code} to continue.\n"
                f"Valid for {CONFIRMATION_EXPIRY_MINUTES} minutes.")

        if command == "CONFIRM" and len(parts) >= 2:
            code = f"CONFIRM {parts[1]}"
            conf = (
                db.query(PendingConfirmation)
                .filter_by(organization_id=organization_id, confirmation_code=code, is_used=False)
                .filter(PendingConfirmation.expires_at > datetime.now(timezone.utc))
                .first()
            )
            if not conf:
                return self._reply(db, phone, organization_id, None,
                    "No valid pending confirmation found or it has expired.")

            case = db.query(Case).filter_by(id=conf.case_id).first()
            if not case:
                return self._reply(db, phone, organization_id, None, "Case not found.")

            # Find user by phone, or create default reviewer user
            user = db.query(User).filter_by(
                organization_id=organization_id, phone_number=phone
            ).first()
            if not user:
                user = db.query(User).filter_by(organization_id=organization_id).first()
            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    organization_id=organization_id,
                    email="reviewer@taxpulse.internal",
                    full_name="WhatsApp Reviewer",
                    role="REVIEWER",
                    phone_number=phone,
                )
                db.add(user)
                db.flush()

            payload = conf.action_payload or {}
            target_status = payload.get("target_status", "IN_REVIEW")

            try:
                self.case_service.transition(db, case, target_status, user, action="review", notes="Confirmed via WhatsApp")
            except Exception as e:
                return self._reply(db, phone, organization_id, case.id, f"Error: {e}")

            conf.is_used = True
            conf.confirmed_at = datetime.now(timezone.utc)

            AuditService.log(
                db,
                organization_id=organization_id,
                event_type="REVIEW_CONFIRMED",
                actor_id=user.id if user else "WHATSAPP",
                entity_type="case",
                entity_id=case.id,
                before_state={"status": case.status},
                after_state={"status": target_status, "via": "WHATSAPP"},
            )

            return self._reply(db, phone, organization_id, case.id,
                f"✅ Case {case.case_number} marked as {target_status}.\n"
                f"Dashboard metrics updated.")

        if command == "CANCEL":
            # Expire all pending confirmations for this org
            pending = (
                db.query(PendingConfirmation)
                .filter_by(organization_id=organization_id, is_used=False)
                .all()
            )
            for p in pending:
                p.is_used = True
            return self._reply(db, phone, organization_id, None, "All pending confirmations cancelled.")

        return self._reply(db, phone, organization_id, None,
            "Unknown command. Reply HELP for available commands.")

    def _reply(
        self, db: Session, phone: str, org_id: str,
        case_id: Optional[str], text: str,
    ) -> str:
        self.provider.send_message(phone, text)
        msg = WhatsAppMessage(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            case_id=case_id,
            recipient_phone=phone,
            direction="OUTBOUND",
            message_body=text,
            status="SENT",
        )
        db.add(msg)
        return text

    @staticmethod
    def get_conversations(
        db: Session, organization_id: str, limit: int = 50,
    ) -> List[WhatsAppMessage]:
        return (
            db.query(WhatsAppMessage)
            .filter_by(organization_id=organization_id)
            .order_by(WhatsAppMessage.sent_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_status() -> Dict[str, Any]:
        provider = _get_provider()
        mode = os.environ.get("WHATSAPP_MODE", "DEMO").upper()
        return {
            "mode": mode,
            "provider": provider.name,
            "configured": True,
        }
