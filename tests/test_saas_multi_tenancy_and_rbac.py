import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import SessionLocal, User, Organization, DocumentMetadata
from backend.rag.vector_store import store_chunks, vector_search, delete_document_chunks
from backend.rag.bm25 import get_bm25_index
from backend.rag.engine import get_rag_engine
from backend.rag.ingestion import detect_sections_and_chunk
from backend.auth.jwt import create_access_token

class TestSaaSMultiTenancyAndRBAC(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Seed two distinct organizations
        org_a = cls.db.query(Organization).filter(Organization.id == "tenant-test-a").first()
        if not org_a:
            org_a = Organization(id="tenant-test-a", name="Tenant A Corp", slug="tenant-a")
            cls.db.add(org_a)

        org_b = cls.db.query(Organization).filter(Organization.id == "tenant-test-b").first()
        if not org_b:
            org_b = Organization(id="tenant-test-b", name="Tenant B Corp", slug="tenant-b")
            cls.db.add(org_b)
        cls.db.commit()

        # Seed test users and generate tokens with user.id as sub
        u_admin_a = cls._create_user("admin-a@test.com", "tenant-test-a", "admin")
        u_student_a = cls._create_user("student-a@test.com", "tenant-test-a", "student")
        u_viewer_a = cls._create_user("viewer-a@test.com", "tenant-test-a", "viewer")
        u_admin_b = cls._create_user("admin-b@test.com", "tenant-test-b", "admin")
        u_super = cls._create_user("super@test.com", "tenant-test-a", "super_admin")

        cls.token_admin_a = create_access_token({"sub": u_admin_a.id, "role": u_admin_a.role})
        cls.token_student_a = create_access_token({"sub": u_student_a.id, "role": u_student_a.role})
        cls.token_viewer_a = create_access_token({"sub": u_viewer_a.id, "role": u_viewer_a.role})
        cls.token_admin_b = create_access_token({"sub": u_admin_b.id, "role": u_admin_b.role})
        cls.token_super = create_access_token({"sub": u_super.id, "role": u_super.role})

    @classmethod
    def _create_user(cls, email: str, tenant_id: str, role: str) -> User:
        u = cls.db.query(User).filter(User.email == email).first()
        if not u:
            u = User(id=f"user-{email}", email=email, hashed_password="pw", tenant_id=tenant_id, role=role)
            cls.db.add(u)
        else:
            u.tenant_id = tenant_id
            u.role = role
        cls.db.commit()
        cls.db.refresh(u)
        return u

    @classmethod
    def tearDownClass(cls):
        # Cleanup test chunks
        delete_document_chunks("doc-tenant-a-01")
        delete_document_chunks("doc-tenant-b-01")
        cls.db.close()

    def test_vector_search_tenant_isolation(self):
        # Index chunks specifically for Tenant A and Tenant B
        chunks_a = [{
            "chunk_id": "chunk_ta_01",
            "document_id": "doc-tenant-a-01",
            "document_title": "Tenant A Secret Policy",
            "text": "Tenant A confidential revenue benefits and eligibility procedures.",
            "status": "active",
            "tenant_id": "tenant-test-a"
        }]
        chunks_b = [{
            "chunk_id": "chunk_tb_01",
            "document_id": "doc-tenant-b-01",
            "document_title": "Tenant B Secret Policy",
            "text": "Tenant B confidential revenue benefits and eligibility procedures.",
            "status": "active",
            "tenant_id": "tenant-test-b"
        }]

        store_chunks(chunks_a)
        store_chunks(chunks_b)

        # Search as Tenant A
        res_a = vector_search("confidential revenue benefits", top_k=5, tenant_id="tenant-test-a")
        res_a_ids = [r["chunk_id"] for r in res_a]
        self.assertIn("chunk_ta_01", res_a_ids)
        self.assertNotIn("chunk_tb_01", res_a_ids)

        # Search as Tenant B
        res_b = vector_search("confidential revenue benefits", top_k=5, tenant_id="tenant-test-b")
        res_b_ids = [r["chunk_id"] for r in res_b]
        self.assertIn("chunk_tb_01", res_b_ids)
        self.assertNotIn("chunk_ta_01", res_b_ids)

    def test_bm25_search_tenant_isolation(self):
        bm25 = get_bm25_index()
        # Search BM25 with tenant filters
        res_a = bm25.search("confidential revenue benefits", top_k=5, filters={"tenant_id": "tenant-test-a"})
        for doc in res_a:
            self.assertEqual(doc.get("tenant_id"), "tenant-test-a")

        res_b = bm25.search("confidential revenue benefits", top_k=5, filters={"tenant_id": "tenant-test-b"})
        for doc in res_b:
            self.assertEqual(doc.get("tenant_id"), "tenant-test-b")

    def test_engine_process_query_tenant_isolation(self):
        engine = get_rag_engine()
        # Process query for Tenant A
        res_a = engine.process_query("confidential revenue benefits", tenant_id="tenant-test-a")
        sources_a = res_a.get("sources", [])
        for s in sources_a:
            self.assertEqual(s.get("tenant_id", "tenant-test-a"), "tenant-test-a")
            self.assertNotEqual(s.get("document_id"), "doc-tenant-b-01")

    def test_rbac_roles_permissions(self):
        # Student cannot access admin endpoints
        r_stud = self.client.get("/api/v1/admin/documents", headers={"Authorization": f"Bearer {self.token_student_a}"})
        self.assertEqual(r_stud.status_code, 403)

        # Viewer cannot access admin endpoints
        r_view = self.client.get("/api/v1/admin/documents", headers={"Authorization": f"Bearer {self.token_viewer_a}"})
        self.assertEqual(r_view.status_code, 403)

        # Admin can access admin endpoints
        r_admin = self.client.get("/api/v1/admin/documents", headers={"Authorization": f"Bearer {self.token_admin_a}"})
        self.assertEqual(r_admin.status_code, 200)

        # Super admin can access admin endpoints
        r_super = self.client.get("/api/v1/admin/documents", headers={"Authorization": f"Bearer {self.token_super}"})
        self.assertEqual(r_super.status_code, 200)

    def test_tenant_user_list_isolation(self):
        # Admin A should only see users of Tenant A
        r = self.client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {self.token_admin_a}"})
        self.assertEqual(r.status_code, 200)
        users = r.json()
        for u in users:
            self.assertEqual(u["tenant_id"], "tenant-test-a")
        emails = [u["email"] for u in users]
        self.assertIn("admin-a@test.com", emails)
        self.assertNotIn("admin-b@test.com", emails)

    def test_detect_sections_and_chunk_tenant_metadata(self):
        pages = [{"page_num": 1, "text": "Eligibility criteria for Tenant A support scheme."}]
        chunks = detect_sections_and_chunk(
            pages=pages,
            doc_id="doc-test-ta",
            doc_title="Policy TA",
            department="Finance",
            tenant_id="tenant-test-a"
        )
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["tenant_id"], "tenant-test-a")

if __name__ == "__main__":
    unittest.main()
