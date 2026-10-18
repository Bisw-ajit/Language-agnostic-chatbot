import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import SessionLocal, User
from backend.observability import log_audit_event, get_audit_logs, export_prometheus_text
from backend.auth.jwt import create_access_token

class TestObservabilityAndProbes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Seed admin and student
        admin = cls.db.query(User).filter(User.email == "admin@demo.com").first()
        student = cls.db.query(User).filter(User.email == "student@demo.com").first()
        cls.admin_token = create_access_token({"sub": admin.id, "role": admin.role})
        cls.student_token = create_access_token({"sub": student.id, "role": student.role})

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_health_and_healthz_probes(self):
        for path in ["/health", "/healthz"]:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data["status"], "ok")
            self.assertIn("version", data)

    def test_liveness_and_livez_probes(self):
        for path in ["/liveness", "/livez"]:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data["status"], "alive")

    def test_readiness_and_readyz_probes(self):
        for path in ["/readiness", "/readyz"]:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data["status"], "ready")
            self.assertEqual(data["database"], "ok")
            self.assertIn("ok", data["vector_store"])
            self.assertIn("ok", data["bm25_index"])

    def test_prometheus_metrics_exposition(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/plain", r.headers.get("content-type", ""))
        body = r.text
        self.assertIn("# HELP http_requests_total", body)
        self.assertIn("# TYPE http_requests_total counter", body)
        self.assertIn("# HELP process_uptime_seconds", body)
        self.assertIn("process_uptime_seconds", body)

    def test_request_tracing_headers(self):
        r = self.client.get("/health")
        self.assertIn("X-Request-ID", r.headers)
        self.assertIn("X-Response-Time-Ms", r.headers)
        # Verify latency is a valid float
        latency = float(r.headers["X-Response-Time-Ms"])
        self.assertGreaterEqual(latency, 0.0)

    def test_audit_logging_and_tenant_scoping(self):
        # Emit an audit event for test
        log_audit_event(
            event_type="TEST_SECURITY_EVENT",
            actor_id="test-actor",
            tenant_id="default-tenant",
            action="probe_check",
            status="SUCCESS",
            details={"ip": "127.0.0.1"}
        )

        logs = get_audit_logs(tenant_id="default-tenant", limit=10)
        self.assertGreater(len(logs), 0)
        self.assertEqual(logs[0]["event_type"], "TEST_SECURITY_EVENT")
        self.assertEqual(logs[0]["status"], "SUCCESS")

        # Admin access to /audit-logs endpoint
        r_admin = self.client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(r_admin.status_code, 200)
        self.assertIn("audit_logs", r_admin.json())

        # Student forbidden from /audit-logs
        r_stud = self.client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {self.student_token}"})
        self.assertEqual(r_stud.status_code, 403)

if __name__ == "__main__":
    unittest.main()
