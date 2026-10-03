import os
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models import (
    Base,
    Organization,
    User,
    TaxRule,
)


def seed_database(db: Session) -> dict:
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # 1. Create or get organization
    org = db.query(Organization).filter_by(slug="taxpulse-org").first()
    if not org:
        org = Organization(
            name="TaxPulse Global Enterprises",
            slug="taxpulse-org",
            tax_identifier="GSTIN-27AAACT2727Q1ZB",
        )
        db.add(org)
        db.flush()

    # 2. Four demo users
    password = os.environ.get("DEMO_USER_PASSWORD", "TaxPulse@Demo2026!")

    users_spec = [
        {"email": "admin@taxpulse.ai", "name": "Admin User", "role": "ADMIN"},
        {"email": "accountant@taxpulse.ai", "name": "Accountant User", "role": "ACCOUNTANT"},
        {"email": "reviewer@taxpulse.ai", "name": "Reviewer User", "role": "REVIEWER"},
        {"email": "viewer@taxpulse.ai", "name": "Viewer User", "role": "VIEWER"},
    ]

    created_users = []
    for spec in users_spec:
        user = db.query(User).filter_by(organization_id=org.id, email=spec["email"]).first()
        if not user:
            user = User(
                organization_id=org.id,
                email=spec["email"],
                full_name=spec["name"],
                role=spec["role"],
                password_hash=password,
                is_active=True,
            )
            db.add(user)
        created_users.append({"email": spec["email"], "role": spec["role"], "password": password})

    # 3. Default tax rules marked demo
    default_rules = [
        {
            "tax_type": "GST",
            "jurisdiction": "IN-MH",
            "rate": Decimal("0.1800"),
            "effective_from": date(2024, 1, 1),
        },
        {
            "tax_type": "GST",
            "jurisdiction": "IN-MH",
            "rate": Decimal("0.1200"),
            "effective_from": date(2024, 1, 1),
        },
        {
            "tax_type": "GST",
            "jurisdiction": "IN-MH",
            "rate": Decimal("0.0500"),
            "effective_from": date(2024, 1, 1),
        },
        {
            "tax_type": "GST",
            "jurisdiction": "IN-MH",
            "rate": Decimal("0.0000"),
            "effective_from": date(2024, 1, 1),
        },
        {
            "tax_type": "SALES_TAX",
            "jurisdiction": "US-TX",
            "rate": Decimal("0.0825"),
            "effective_from": date(2024, 1, 1),
        },
    ]

    for r in default_rules:
        existing = (
            db.query(TaxRule)
            .filter_by(
                organization_id=org.id,
                tax_type=r["tax_type"],
                jurisdiction=r["jurisdiction"],
                rate=r["rate"],
            )
            .first()
        )
        if not existing:
            rule = TaxRule(
                organization_id=org.id,
                tax_type=r["tax_type"],
                jurisdiction=r["jurisdiction"],
                rate=r["rate"],
                effective_from=r["effective_from"],
                is_active=True,
                is_demo=True,
            )
            db.add(rule)

    db.commit()

    return {
        "organization": {"id": org.id, "slug": org.slug, "name": org.name},
        "users": created_users,
        "tax_rules_count": len(default_rules),
    }


def main():
    db = SessionLocal()
    try:
        result = seed_database(db)
        print("=" * 60)
        print("TaxPulse AI — Database Seeding Successful")
        print("=" * 60)
        print(f"Organization: {result['organization']['name']} (Slug: {result['organization']['slug']})")
        print("\nDemo Credentials (Printed Once):")
        for u in result["users"]:
            print(f"  [{u['role']:<10}] Email: {u['email']:<24} Password: {u['password']}")
        print(f"\nDefault Tax Rules Seeded: {result['tax_rules_count']} (marked demo)")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
