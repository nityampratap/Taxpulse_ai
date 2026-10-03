from httpx import Client


def test_endpoints_are_wired(client: Client):
    """Verify no endpoint returns 501 (all stubs are now wired)."""
    endpoints = [
        ("GET", "/api/v1/transactions"),
        ("GET", "/api/v1/exceptions"),
        ("GET", "/api/v1/cases"),
        ("GET", "/api/v1/tax/rules"),
        ("GET", "/api/v1/vendors"),
        ("GET", "/api/v1/dashboard/metrics"),
        ("GET", "/api/v1/whatsapp/status"),
        ("GET", "/api/v1/audit/events"),
        ("GET", "/api/v1/settings"),
    ]

    for method, path in endpoints:
        response = client.get(path)
        assert response.status_code != 501, f"{method} {path} still returns 501 (not wired)"
        assert response.status_code in (200, 401, 403), f"Unexpected {response.status_code} for {method} {path}"
        assert "x-request-id" in response.headers


def test_not_found_error_format(client: Client):
    response = client.get("/api/v1/nonexistent-route-999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "x-request-id" in response.headers


def test_secret_redaction_in_middleware(client: Client):
    # Sending sensitive query param should not crash and should complete
    response = client.get("/api/health?api_key=secret-token-12345&foo=bar")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
