"""Vendors router: list, detail, history."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import Vendor, Organization, Invoice, Case, ReconciliationResult

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("")
def list_vendors(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return []
    vendors = db.query(Vendor).filter_by(organization_id=org.id).all()
    return [
        {
            "id": v.id, "name": v.name, "normalized_name": v.normalized_name,
            "tax_identifier": v.tax_identifier, "risk_tier": v.risk_tier,
            "dispute_count": v.dispute_count,
        }
        for v in vendors
    ]


@router.get("/{vendor_id}")
def get_vendor(vendor_id: str, db: Session = Depends(get_db)):
    v = db.query(Vendor).filter_by(id=vendor_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    invoice_count = db.query(Invoice).filter_by(vendor_id=v.id).count()
    total_amount = db.query(func.sum(Invoice.total_amount)).filter_by(vendor_id=v.id).scalar()
    return {
        "id": v.id, "name": v.name, "normalized_name": v.normalized_name,
        "tax_identifier": v.tax_identifier, "risk_tier": v.risk_tier,
        "dispute_count": v.dispute_count, "invoice_count": invoice_count,
        "total_amount": str(total_amount or 0),
    }


@router.get("/{vendor_id}/history")
def vendor_history(vendor_id: str, db: Session = Depends(get_db)):
    v = db.query(Vendor).filter_by(id=vendor_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    invoices = db.query(Invoice).filter_by(vendor_id=v.id).order_by(Invoice.invoice_date.desc()).limit(50).all()
    return [
        {
            "invoice_number": i.invoice_number, "date": str(i.invoice_date),
            "total": str(i.total_amount), "tax": str(i.tax_amount), "status": i.status,
        }
        for i in invoices
    ]
