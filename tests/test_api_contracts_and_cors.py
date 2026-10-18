import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestApiContractsAndCORS(unittest.TestCase):
    """
    Phase 7 Test Suite: Validates CORS headers, error response payload schemas,
    request tracing headers, and API contract conformance.
    """

    def test_cors_preflight_headers(self):
        """Verify CORS preflight OPTIONS request returns required access control headers."""
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        res = client.options("/api/v1/chat", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("access-control-allow-origin", res.headers)
        self.assertEqual(res.headers["access-control-allow-origin"], "http://localhost:5173")

    def test_cors_exposed_headers(self):
        """Verify CORS response exposes X-Request-ID and X-Response-Time-Ms."""
        headers = {"Origin": "http://localhost:5173"}
        res = client.get("/healthz", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("access-control-expose-headers", res.headers)
        exposed = [h.strip().lower() for h in res.headers["access-control-expose-headers"].split(",")]
        self.assertIn("x-request-id", exposed)
        self.assertIn("x-response-time-ms", exposed)

    def test_request_tracing_headers_on_all_responses(self):
        """Verify every response returns valid X-Request-ID and numeric X-Response-Time-Ms."""
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertIn("X-Request-ID", res.headers)
        self.assertIn("X-Response-Time-Ms", res.headers)
        self.assertTrue(len(res.headers["X-Request-ID"]) > 10)
        self.assertTrue(float(res.headers["X-Response-Time-Ms"]) >= 0.0)

    def test_standardized_error_payload_on_404(self):
        """Verify 404 responses conform to standardized error payload schema."""
        res = client.get("/api/v1/non-existent-endpoint-xyz")
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertIn("detail", data)
        self.assertIn("error", data)
        self.assertIn("code", data["error"])
        self.assertEqual(data["error"]["code"], 404)
        self.assertIn("message", data["error"])
        self.assertIn("request_id", data["error"])
        self.assertIn("request_id", data)

    def test_standardized_error_payload_on_422(self):
        """Verify 422 validation errors conform to standardized error payload schema."""
        login_res = client.post("/api/v1/auth/login", json={
            "email": "student@demo.com",
            "password": "demo123"
        })
        token = login_res.json()["access_token"]
        # Missing required 'message' field in chat request
        res = client.post(
            "/api/v1/chat",
            json={"invalid_field": 123},
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(res.status_code, 422)
        data = res.json()
        self.assertIn("detail", data)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], 422)
        self.assertIn("message", data["error"])
        self.assertIn("details", data["error"])
        self.assertIn("request_id", data)

    def test_standardized_error_payload_on_401(self):
        """Verify 401 unauthorized errors conform to standardized error schema."""
        res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.xyz"})
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertIn("detail", data)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], 401)
        self.assertIn("message", data["error"])
        self.assertIn("request_id", data)

    def test_auth_login_contract_contains_tenant_and_user_meta(self):
        """Verify /auth/login contract returns access_token, role, user_id, and tenant_id."""
        res = client.post("/api/v1/auth/login", json={
            "email": "student@demo.com",
            "password": "demo123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data.get("token_type"), "bearer")
        self.assertEqual(data.get("role"), "student")
        self.assertIn("user_id", data)
        self.assertIn("tenant_id", data)

    def test_auth_me_contract(self):
        """Verify /auth/me returns id, email, role, and tenant_id."""
        login_res = client.post("/api/v1/auth/login", json={
            "email": "student@demo.com",
            "password": "demo123"
        })
        token = login_res.json()["access_token"]
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["email"], "student@demo.com")
        self.assertEqual(data["role"], "student")
        self.assertIn("tenant_id", data)

if __name__ == "__main__":
    unittest.main()
