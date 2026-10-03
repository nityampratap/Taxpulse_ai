"""WhatsApp router: status, send, conversations, webhook, simulator."""
import hashlib
import hmac
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Case, Organization
from app.services.whatsapp import WhatsAppService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
_svc = WhatsAppService()


class SendRequest(BaseModel):
    case_id: str
    phone: str


class SimulateRequest(BaseModel):
    phone: str
    message: str


@router.get("/status")
def whatsapp_status():
    return _svc.get_status()


@router.post("/send")
def send_alert(body: SendRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(
        (Case.id == body.case_id) | (Case.case_number == body.case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    msg = _svc.send_alert(db, case, body.phone, case.organization_id)
    db.commit()
    return {"status": "sent", "message_id": msg.id}


@router.get("/conversations")
def get_conversations(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return []
    messages = _svc.get_conversations(db, org.id)
    return [
        {
            "id": m.id, "direction": m.direction, "message_body": m.message_body,
            "status": m.status, "phone": m.recipient_phone, "sent_at": str(m.sent_at),
            "case_id": m.case_id,
        }
        for m in messages
    ]


@router.post("/simulate-inbound")
def simulate_inbound(body: SimulateRequest, db: Session = Depends(get_db)):
    mode = os.environ.get("WHATSAPP_MODE", "DEMO").upper()
    if mode == "LIVE":
        raise HTTPException(status_code=403, detail="Simulator disabled in LIVE mode")
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")
    response = _svc.handle_inbound(db, body.phone, body.message, org.id)
    db.commit()
    return {"response": response}


@router.get("/webhook")
def webhook_verify(request: Request):
    """Meta webhook verification challenge."""
    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge", "")
    if mode == "subscribe" and token == verify_token:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def webhook_receive(request: Request, db: Session = Depends(get_db)):
    """Inbound webhook with HMAC verification."""
    app_secret = os.environ.get("WHATSAPP_APP_SECRET", "")
    if app_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        body_bytes = await request.body()
        expected = "sha256=" + hmac.new(
            app_secret.encode(), body_bytes, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid signature")

    return {"status": "ok"}
