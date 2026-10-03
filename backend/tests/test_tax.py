from datetime import date
from decimal import Decimal
import pytest
from app.services.tax import TaxRateService, TaxEngine
from app.models.models import Organization, TaxRule


def test_tax_rate_service_lookup(db):
    org = Organization(name="Tax Org", slug="tax-org-test", tax_identifier="T123")
    db.add(org)
    db.flush()

    rule1 = TaxRule(
        organization_id=org.id, tax_type="GST", jurisdiction="IN-MH",
        rate=Decimal("0.1800"), effective_from=date(2025, 1, 1),
        effective_to=date(2025, 12, 31), is_active=True,
    )
    rule2 = TaxRule(
        organization_id=org.id, tax_type="GST", jurisdiction="IN-MH",
        rate=Decimal("0.2000"), effective_from=date(2026, 1, 1),
        effective_to=None, is_active=True,
    )
    db.add_all([rule1, rule2])
    db.flush()

    # Query in 2025
    r2025 = TaxRateService.get_rate(db, org.id, on_date=date(2025, 6, 1))
    assert r2025 is not None
    assert r2025.rate == Decimal("0.1800")

    # Query in 2026
    r2026 = TaxRateService.get_rate(db, org.id, on_date=date(2026, 3, 15))
    assert r2026 is not None
    assert r2026.rate == Decimal("0.2000")


def test_tax_engine_verify():
    # Exact calculation
    res = TaxEngine.verify(Decimal("1000.00"), Decimal("180.00"), Decimal("0.1800"))
    assert res["expected_tax"] == Decimal("180.00")
    assert res["variance"] == Decimal("0.00")
    assert res["has_variance"] is False
    assert res["potential_exposure"] == Decimal("0.00")

    # Overpayment (TX-10482 scenario: 97500 @ 18% -> 17550 expected, 18000 recorded)
    res_tx = TaxEngine.verify(Decimal("97500.00"), Decimal("18000.00"), Decimal("0.1800"))
    assert res_tx["expected_tax"] == Decimal("17550.00")
    assert res_tx["recorded_tax"] == Decimal("18000.00")
    assert res_tx["variance"] == Decimal("450.00")
    assert res_tx["has_variance"] is True
    assert res_tx["direction"] == "OVER"
    assert res_tx["potential_exposure"] == Decimal("450.00")

    # Underpayment: 50000 @ 18% -> 9000 expected, 6000 recorded
    res_under = TaxEngine.verify(Decimal("50000.00"), Decimal("6000.00"), Decimal("0.1800"))
    assert res_under["expected_tax"] == Decimal("9000.00")
    assert res_under["variance"] == Decimal("-3000.00")
    assert res_under["potential_liability"] == Decimal("3000.00")
    assert res_under["potential_exposure"] == Decimal("3000.00")
    assert res_under["direction"] == "UNDER"
