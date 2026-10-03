"""Transactions router: list, detail, create."""
from decimal import Decimal
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Transaction, Organization

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("")
def list_transactions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return {"transactions": [], "total": 0}
    q = db.query(Transaction).filter_by(organization_id=org.id)
    total = q.count()
    txns = q.order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit).all()
    return {
        "transactions": [
            {
                "id": t.id, "reference_id": t.reference_id, "source": t.source,
                "transaction_date": str(t.transaction_date), "amount": str(t.amount),
                "currency": t.currency, "description": t.description,
                "counterparty_name": t.counterparty_name,
            }
            for t in txns
        ],
        "total": total,
    }


@router.get("/{txn_id}")
def get_transaction(txn_id: str, db: Session = Depends(get_db)):
    t = db.query(Transaction).filter_by(id=txn_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "id": t.id, "reference_id": t.reference_id, "source": t.source,
        "transaction_date": str(t.transaction_date), "amount": str(t.amount),
        "currency": t.currency, "description": t.description,
        "counterparty_name": t.counterparty_name,
    }


class CreateTransaction(BaseModel):
    reference_id: str
    source: str = "MANUAL"
    transaction_date: str
    amount: str
    currency: str = "INR"
    description: Optional[str] = None
    counterparty_name: Optional[str] = None


@router.post("", status_code=201)
def create_transaction(body: CreateTransaction, db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")
    from datetime import date
    t = Transaction(
        id=str(uuid.uuid4()), organization_id=org.id,
        reference_id=body.reference_id, source=body.source,
        transaction_date=date.fromisoformat(body.transaction_date),
        amount=Decimal(body.amount), currency=body.currency,
        description=body.description, counterparty_name=body.counterparty_name,
    )
    db.add(t)
    db.commit()
    return {"id": t.id}
