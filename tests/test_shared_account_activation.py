from tests.payload_tools.auth import build_signup_payload, build_login_payload
import pytest


def test_account_deactivate_and_activate(test_client, auth_header):
    # Deactivate account
    resp = test_client.post("/roles/shared/account/deactivate", headers=auth_header)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert "deactivated" in data["message"].lower()

    # Try to access a protected endpoint (should fail)
    resp2 = test_client.patch("/roles/shared/account/update", json={}, headers=auth_header)
    assert resp2.status_code in (400, 401)
    assert "inactive account" in resp2.text.lower()

    # Reactivate account
    # Need to login again to get a new token (since the old one is now blocked)
    signup_payload = build_signup_payload()
    test_client.post("/auth/signup", json=signup_payload)
    login_resp = test_client.post("/auth/login", json=build_login_payload(signup_payload["email"], signup_payload["password"]))
    token = login_resp.json()["access_token"]
    header = {"Authorization": f"Bearer {token}"}

    # Deactivate again
    test_client.post("/roles/shared/account/deactivate", headers=header)
    # Activate
    resp3 = test_client.post("/roles/shared/account/activate", headers=header)
    assert resp3.status_code == 200, resp3.text
    data3 = resp3.json()
    assert data3["success"] is True
    assert "activated" in data3["message"].lower()

    # Should be able to access protected endpoint again
    resp4 = test_client.patch("/roles/shared/account/update", json={}, headers=header)
    assert resp4.status_code == 200
