from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

database_url = settings.DATABASE_URL or "sqlite:///./taxpulse.db"

try:
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=False,
        future=True,
    )
except (ModuleNotFoundError, ImportError, Exception):
    # SQLite fallback for local development per AGENTS.md
    database_url = settings.SQLITE_FALLBACK_URL or "sqlite:///./taxpulse.db"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=False,
        future=True,
    )

# Enable SQLite foreign key constraint enforcement
if database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
