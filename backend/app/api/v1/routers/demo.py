from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from scripts.generate_demo_data import seed_demo_data_to_db
from app.models import (
    Organization,
    Vendor,
    Invoice,
    Transaction,
    Payment,
    LedgerEntry,
    TaxRule,
    ImportBatch,
    Case,
    ReconciliationResult,
    ReconciliationRun,
)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_demo_data(db: Session = Depends(get_db)):
    """
    Generate deterministic demo dataset (seed 42) into the database.
    """
    metadata = seed_demo_data_to_db(db)
    return {
        "status": "success",
        "message": "Demo data generated successfully",
        "metadata": metadata,
    }


@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_demo_data(db: Session = Depends(get_db)):
    """
    Purge all generated demo data from the database.
    """
    org = db.query(Organization).filter_by(slug="taxpulse-org").first()
    if org:
        db.query(Case).filter_by(organization_id=org.id).delete()
        db.query(ReconciliationResult).filter_by(organization_id=org.id).delete()
        db.query(ReconciliationRun).filter_by(organization_id=org.id).delete()
        db.query(Payment).filter_by(organization_id=org.id).delete()
        db.query(Invoice).filter_by(organization_id=org.id).delete()
        db.query(Transaction).filter_by(organization_id=org.id).delete()
        db.query(LedgerEntry).filter_by(organization_id=org.id).delete()
        db.query(ImportBatch).filter_by(organization_id=org.id).delete()
        db.query(TaxRule).filter_by(organization_id=org.id, is_demo=True).delete()
        db.commit()

    return {
        "status": "success",
        "message": "Demo data reset successfully",
    }

