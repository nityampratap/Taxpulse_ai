"""
TaxPulse AI - Environment & Connectivity Doctor
Tests database connectivity, AI keys, WhatsApp credentials, and Supabase storage.
Prints a clean summary checklist with PASS/FAIL/WARN.
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

# Load root .env
root_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(root_env)


def check():
    print("=" * 60)
    print(" TAXPULSE AI - SYSTEM READINESS & ENVIRONMENT CHECK")
    print("=" * 60)

    checks = []

    # 1. Database Connection
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./taxpulse.db")
    try:
        from app.db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_type = "PostgreSQL" if "postgresql" in db_url else "SQLite (Local/Offline)"
        checks.append(("Database Connection", "PASS", f"Connected to {db_type}"))
    except Exception as e:
        checks.append(("Database Connection", "FAIL", str(e)))

    # 2. JWT Configuration
    jwt_secret = os.environ.get("JWT_SECRET", "")
    if jwt_secret and jwt_secret != "UPDATE_ME" and len(jwt_secret) >= 32:
        checks.append(("JWT Authentication", "PASS", "Secret key configured (>= 32 chars)"))
    elif jwt_secret and jwt_secret != "UPDATE_ME":
        checks.append(("JWT Authentication", "WARN", "Secret key configured but short (< 32 chars)"))
    else:
        checks.append(("JWT Authentication", "WARN", "JWT_SECRET is placeholder; using dev fallback"))

    # 3. AI Providers
    groq_key = os.environ.get("GROQ_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    if groq_key and groq_key != "UPDATE_ME":
        checks.append(("AI: Groq Provider", "PASS", f"Configured (model: {os.environ.get('GROQ_MODEL', 'default')})"))
    else:
        checks.append(("AI: Groq Provider", "WARN", "Not configured; will fallback to Gemini/Mock"))

    if gemini_key and gemini_key != "UPDATE_ME":
        checks.append(("AI: Gemini Provider", "PASS", f"Configured (model: {os.environ.get('GEMINI_MODEL', 'default')})"))
    else:
        checks.append(("AI: Gemini Provider", "WARN", "Not configured; will fallback to Mock"))

    checks.append(("AI: Mock Template Provider", "PASS", "Deterministic template engine active"))

    # 4. WhatsApp Integration
    wa_mode = os.environ.get("WHATSAPP_MODE", "DEMO").upper()
    if wa_mode == "LIVE":
        wa_token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
        wa_phone = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        if wa_token and wa_token != "UPDATE_ME" and wa_phone and wa_phone != "UPDATE_ME":
            checks.append(("WhatsApp Integration", "PASS", "LIVE mode configured with Meta Cloud API"))
        else:
            checks.append(("WhatsApp Integration", "FAIL", "LIVE mode selected but credentials missing"))
    else:
        checks.append(("WhatsApp Integration", "PASS", "DEMO mode active (in-app interactive simulator)"))

    # 5. Storage
    storage_provider = os.environ.get("STORAGE_PROVIDER", "local").lower()
    if storage_provider == "supabase":
        supabase_url = os.environ.get("SUPABASE_URL", "")
        if supabase_url and supabase_url != "UPDATE_ME":
            checks.append(("Storage Provider", "PASS", "Supabase Storage bucket configured"))
        else:
            checks.append(("Storage Provider", "WARN", "Supabase storage selected but URL placeholder"))
    else:
        checks.append(("Storage Provider", "PASS", "Local filesystem / memory storage active"))

    # Print Report
    print(f"\n{'Component':<28} | {'Status':<6} | {'Details'}")
    print("-" * 60)
    for comp, status, details in checks:
        icon = "[✓]" if status == "PASS" else ("[x]" if status == "FAIL" else "[!]")
        print(f"{comp:<28} | {status:<6} | {details}")

    print("=" * 60)
    has_fail = any(s == "FAIL" for _, s, _ in checks)
    if has_fail:
        print("RESULT: FAILED - Please resolve errors above.")
        sys.exit(1)
    else:
        print("RESULT: PASSED - System is ready for operation.")
        sys.exit(0)


if __name__ == "__main__":
    check()
