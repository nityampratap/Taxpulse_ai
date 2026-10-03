from decimal import Decimal
import pytest
from httpx import Client


def test_full_demo_story_e2e(client: Client):
    """
    End-to-end integration test of the full demo flow:
    1. Generate demo data
    2. Run reconciliation
    3. Open Case TX-10482
    4. AI explain TX-10482
    5. WhatsApp alert dispatch
    6. Inbound EXPLAIN via WhatsApp simulator
    7. Inbound REVIEW via WhatsApp simulator
    8. Inbound CONFIRM via WhatsApp simulator
    9. Verify dashboard count updated
    10. Verify audit rows recorded
    """
    # 1. Generate demo data
    gen_resp = client.post("/api/v1/demo/generate")
    assert gen_resp.status_code == 201
    assert gen_resp.json()["status"] == "success"

    # 2. Run reconciliation
    recon_resp = client.post("/api/v1/reconciliation/run", json={})
    assert recon_resp.status_code == 202
    recon_data = recon_resp.json()
    assert recon_data["status"] == "COMPLETED"
    assert recon_data["total_processed"] == 105
    assert recon_data["cases_created"] > 0

    # 3. Open Case TX-10482
    case_resp = client.get("/api/v1/cases/TX-10482")
    assert case_resp.status_code == 200
    case_data = case_resp.json()
    assert case_data["case_number"] == "TX-10482"
    assert case_data["status"] == "OPEN"
    assert case_data["priority"] == "HIGH"
    assert case_data["risk_score"] == "62.00"
    assert case_data["tax_impact"] == "450.00"
    assert case_data["financial_exposure"] == "100000.00"

    # 4. Invoke AI explain on TX-10482
    ai_resp = client.post("/api/v1/ai/explain-case", json={"case_id": "TX-10482"})
    assert ai_resp.status_code == 200
    ai_data = ai_resp.json()
    assert "summary" in ai_data
    assert "450" in ai_data["summary"]

    # 5. Dispatch WhatsApp alert
    alert_resp = client.post("/api/v1/whatsapp/send", json={
        "case_id": "TX-10482",
        "phone": "+919876543210",
    })
    assert alert_resp.status_code == 200
    assert alert_resp.json()["status"] == "sent"

    # 6. Inbound EXPLAIN via simulator
    explain_resp = client.post("/api/v1/whatsapp/simulate-inbound", json={
        "phone": "+919876543210",
        "message": "EXPLAIN TX-10482",
    })
    assert explain_resp.status_code == 200
    assert "TAXPULSE AI ANALYSIS" in explain_resp.json()["response"]

    # 7. Inbound REVIEW via simulator
    review_resp = client.post("/api/v1/whatsapp/simulate-inbound", json={
        "phone": "+919876543210",
        "message": "REVIEW TX-10482",
    })
    assert review_resp.status_code == 200
    assert "CONFIRM TX-10482" in review_resp.json()["response"]

    # 8. Inbound CONFIRM via simulator
    confirm_resp = client.post("/api/v1/whatsapp/simulate-inbound", json={
        "phone": "+919876543210",
        "message": "CONFIRM TX-10482",
    })
    assert confirm_resp.status_code == 200
    assert "marked as IN_REVIEW" in confirm_resp.json()["response"]

    # Verify case status updated in DB
    updated_case_resp = client.get("/api/v1/cases/TX-10482")
    assert updated_case_resp.json()["status"] == "IN_REVIEW"

    # 9. Verify dashboard metrics
    metrics_resp = client.get("/api/v1/dashboard/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_transactions"] == 105
    assert metrics["matched"] > 0
    assert metrics["high_risk"] > 0

    # 10. Verify audit rows recorded
    audit_resp = client.get("/api/v1/audit/events")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 4
    event_types = [e["event_type"] for e in events]
    assert "RECONCILIATION_RUN" in event_types
    assert "CASE_CREATED" in event_types
    assert "AI_ANALYSIS_COMPLETED" in event_types
    assert "WHATSAPP_ALERT_SENT" in event_types
