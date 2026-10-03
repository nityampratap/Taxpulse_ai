"""Imports router: file upload, batch listing."""
import hashlib
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import ImportBatch, Organization
from app.services.audit import AuditService

router = APIRouter(prefix="/imports", tags=["imports"])

ALLOWED_TYPES = {"text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 "application/pdf", "application/vnd.ms-excel"}
MAX_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    source_type = {"csv": "CSV", "xlsx": "EXCEL", "xls": "EXCEL", "pdf": "PDF"}.get(ext, "CSV")

    file_hash = hashlib.sha256(content).hexdigest()
    existing = db.query(ImportBatch).filter_by(organization_id=org.id, file_hash=file_hash).first()
    if existing:
        return {"batch_id": existing.id, "status": "duplicate", "message": "File already imported"}

    batch = ImportBatch(
        id=str(uuid.uuid4()), organization_id=org.id,
        source_type=source_type, file_name=file.filename or "upload",
        file_hash=file_hash, row_count=0, status="PARSED",
    )
    db.add(batch)
    AuditService.log(db, organization_id=org.id, event_type="IMPORT_COMPLETED",
                     actor_id="SYSTEM", entity_type="import_batch", entity_id=batch.id,
                     after_state={"file": file.filename, "type": source_type})
    db.commit()
    return {"batch_id": batch.id, "status": "parsed", "source_type": source_type}


@router.get("/batches")
def list_batches(db: Session = Depends(get_db)):
    org = db.query(Organization).first()
    if not org:
        return []
    batches = db.query(ImportBatch).filter_by(organization_id=org.id).order_by(
        ImportBatch.ingested_at.desc()).all()
    return [
        {"id": b.id, "file_name": b.file_name, "source_type": b.source_type,
         "status": b.status, "row_count": b.row_count, "ingested_at": str(b.ingested_at)}
        for b in batches
    ]


@router.get("/{batch_id}")
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.query(ImportBatch).filter_by(id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {
        "id": batch.id, "file_name": batch.file_name, "source_type": batch.source_type,
        "status": batch.status, "row_count": batch.row_count,
        "file_hash": batch.file_hash, "ingested_at": str(batch.ingested_at),
    }
