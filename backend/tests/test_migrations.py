import os
import tempfile
from pathlib import Path
import pytest
from alembic.config import Config
from alembic import command

BACKEND_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_INI = str(BACKEND_DIR / "alembic.ini")


def test_alembic_upgrade_downgrade_cycle():
    # Use temporary sqlite database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        sqlite_url = f"sqlite:///{db_path}"
        os.environ["DATABASE_URL"] = sqlite_url

        alembic_cfg = Config(ALEMBIC_INI)
        alembic_cfg.set_main_option("sqlalchemy.url", sqlite_url)

        # 1. Migrate up to head
        command.upgrade(alembic_cfg, "head")

        # 2. Migrate down to base
        command.downgrade(alembic_cfg, "base")

        # 3. Migrate back up to head
        command.upgrade(alembic_cfg, "head")

    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
