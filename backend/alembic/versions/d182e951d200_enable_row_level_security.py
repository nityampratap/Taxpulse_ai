"""enable row level security on all public tables

Revision ID: d182e951d200
Revises: c955d840c1a6
Create Date: 2026-10-03 22:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd182e951d200'
down_revision: Union[str, Sequence[str], None] = 'c955d840c1a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "organizations",
    "users",
    "vendors",
    "invoices",
    "transactions",
    "payments",
    "ledger_entries",
    "tax_rules",
    "import_batches",
    "reconciliation_runs",
    "reconciliation_results",
    "audit_events",
    "anomalies",
    "cases",
    "case_assignments",
    "ai_interactions",
    "whatsapp_messages",
    "pending_confirmations",
]


def upgrade() -> None:
    """Enable Row Level Security on all business tables when on PostgreSQL."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    """Disable Row Level Security when on PostgreSQL."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
