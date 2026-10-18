import os
import sys
import unittest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestProductionContainerization(unittest.TestCase):
    """
    Phase 8 Test Suite: Validates Docker Compose orchestration, multi-stage Dockerfiles,
    container healthchecks, and Nginx reverse proxy configuration.
    """

    def test_docker_compose_valid_and_services_defined(self):
        """Verify docker-compose.yml has valid syntax and defines db, backend, and frontend."""
        compose_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
        self.assertTrue(os.path.exists(compose_path), "docker-compose.yml must exist")

        with open(compose_path, "r", encoding="utf-8") as f:
            compose_cfg = yaml.safe_load(f)

        self.assertIn("services", compose_cfg)
        services = compose_cfg["services"]
        self.assertIn("db", services)
        self.assertIn("backend", services)
        self.assertIn("frontend", services)

    def test_docker_compose_healthchecks_and_dependencies(self):
        """Verify all services have healthchecks and proper dependency condition ordering."""
        compose_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
        with open(compose_path, "r", encoding="utf-8") as f:
            compose_cfg = yaml.safe_load(f)

        services = compose_cfg["services"]

        # 1. DB healthcheck
        self.assertIn("healthcheck", services["db"])
        self.assertIn("test", services["db"]["healthcheck"])

        # 2. Backend healthcheck + dependency on db
        self.assertIn("healthcheck", services["backend"])
        backend_deps = services["backend"].get("depends_on", {})
        self.assertEqual(backend_deps.get("db", {}).get("condition"), "service_healthy")

        # 3. Frontend healthcheck + dependency on backend
        self.assertIn("healthcheck", services["frontend"])
        frontend_deps = services["frontend"].get("depends_on", {})
        self.assertEqual(frontend_deps.get("backend", {}).get("condition"), "service_healthy")

        # 4. Isolated bridge network and volumes
        self.assertIn("networks", compose_cfg)
        self.assertIn("volumes", compose_cfg)

    def test_backend_dockerfile_multi_stage_and_security(self):
        """Verify backend Dockerfile uses multi-stage build, non-root user, and healthcheck."""
        dockerfile_path = os.path.join(PROJECT_ROOT, "backend", "Dockerfile")
        self.assertTrue(os.path.exists(dockerfile_path))

        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Multi-stage check
        self.assertIn("AS builder", content)
        self.assertIn("AS runner", content)

        # Non-root user check
        self.assertIn("USER chatbot", content)
        self.assertIn("useradd", content)

        # Healthcheck check
        self.assertIn("HEALTHCHECK", content)
        self.assertIn("readyz", content)

        # Language packs for OCR
        self.assertIn("tesseract-ocr-hin", content)
        self.assertIn("tesseract-ocr-ori", content)

        # Port exposition
        self.assertIn("EXPOSE 8000", content)

    def test_frontend_dockerfile_multi_stage_and_healthcheck(self):
        """Verify frontend Dockerfile uses multi-stage build and defines healthcheck."""
        dockerfile_path = os.path.join(PROJECT_ROOT, "frontend", "Dockerfile")
        self.assertTrue(os.path.exists(dockerfile_path))

        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("AS builder", content)
        self.assertIn("AS runner", content)
        self.assertIn("HEALTHCHECK", content)
        self.assertIn("EXPOSE 80", content)

    def test_nginx_conf_security_headers_and_reverse_proxy(self):
        """Verify nginx.conf includes security headers, gzip, and probe reverse proxies."""
        nginx_path = os.path.join(PROJECT_ROOT, "frontend", "nginx.conf")
        self.assertTrue(os.path.exists(nginx_path))

        with open(nginx_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Security headers
        self.assertIn("X-Frame-Options", content)
        self.assertIn("X-Content-Type-Options", content)
        self.assertIn("X-XSS-Protection", content)

        # Gzip compression
        self.assertIn("gzip on", content)

        # Reverse proxy locations
        self.assertIn("location /api", content)
        self.assertIn("http://backend:8000", content)
        self.assertIn("location ~ ^/(health|healthz|livez|readyz|metrics)", content)

if __name__ == "__main__":
    unittest.main()
