from fastapi import APIRouter
from app.api.v1.routers import (
    health,
    auth,
    imports,
    demo,
    transactions,
    reconciliation,
    exceptions,
    cases,
    tax,
    vendors,
    dashboard,
    reports,
    ai,
    whatsapp,
    audit,
    settings,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(imports.router)
api_router.include_router(demo.router)
api_router.include_router(transactions.router)
api_router.include_router(reconciliation.router)
api_router.include_router(exceptions.router)
api_router.include_router(cases.router)
api_router.include_router(tax.router)
api_router.include_router(vendors.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(ai.router)
api_router.include_router(whatsapp.router)
api_router.include_router(audit.router)
api_router.include_router(settings.router)
