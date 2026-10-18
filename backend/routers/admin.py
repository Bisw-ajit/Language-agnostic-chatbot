import os
import re
import uuid
import hashlib
import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from backend.config import get_settings
from backend.models.database import get_db, DocumentMetadata, Message, Conversation, User
from backend.auth.jwt import require_role
from backend.rag.ingestion import process_document_ingestion
from backend.rag.vector_store import delete_document_chunks, archive_document_chunks
from backend.contracts.api_types import DocumentMetadataResponse, DocumentStatusResponse
from backend.observability import log_audit_event, get_audit_logs

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

_settings = get_settings()
UPLOAD_DIR = os.path.abspath(_settings.upload_dir)
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UpdateDocRequest(BaseModel):
    status: str

class ActionRequest(BaseModel):
    action: str

@router.post("/documents")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    department: str = Form(...),
    language: str = Form(...),
    version: str = Form(...),
    title: Optional[str] = Form(None),
    category: str = Form("Scheme"),
    source_type: str = Form("official"),
    authority_level: str = Form("official"),
    source_url: Optional[str] = Form(None),
    publisher: Optional[str] = Form(None),
    publication_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin", "super_admin"))
):
    settings = get_settings()

    # 1. Filename Extension Check
    original_name = file.filename or ""
    if not original_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents (.pdf) are permitted."
        )

    # 2. MIME Content-Type Check
    if file.content_type and file.content_type not in ["application/pdf", "application/x-pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{file.content_type}'. Must be 'application/pdf'."
        )

    content = await file.read()

    # 3. File Size & Empty Check
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size of {settings.max_upload_size_mb} MB."
        )

    # 4. Binary Magic Byte Validation (%PDF)
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF binary header. The uploaded file is not a valid PDF."
        )

    # 5. Malformed PDF Validation via PyMuPDF
    try:
        test_doc = fitz.open(stream=content, filetype="pdf")
        if test_doc.is_encrypted:
            test_doc.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Encrypted or password-protected PDF files cannot be processed."
            )
        if test_doc.page_count == 0:
            test_doc.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF contains 0 pages."
            )
        test_doc.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or unreadable PDF document: {str(e)}"
        )

    # 6. Checksum & Duplicate check
    checksum = hashlib.sha256(content).hexdigest()
    existing_dup = db.query(DocumentMetadata).filter(
        DocumentMetadata.checksum == checksum,
        DocumentMetadata.status.in_(["active", "pending_approval", "pending"])
    ).first()
    if existing_dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate document detected (matches '{existing_dup.title}' v{existing_dup.version})"
        )

    # 7. Safe Filename Sanitization and Path Traversal Prevention
    file_id = str(uuid.uuid4())
    safe_basename = re.sub(r'[^a-zA-Z0-9._-]', '_', os.path.basename(original_name))
    safe_filename = f"{file_id}_{safe_basename}"
    file_path = os.path.abspath(os.path.join(UPLOAD_DIR, safe_filename))

    if not file_path.startswith(UPLOAD_DIR):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal file path detected."
        )

    with open(file_path, "wb") as f:
        f.write(content)
        
    doc_title = title or file.filename.replace(".pdf", "").replace("_", " ")
    doc = DocumentMetadata(
        id=file_id,
        title=doc_title,
        filename=file.filename,
        department=department,
        category=category,
        language=language,
        version=version,
        source_type=source_type,
        authority_level=authority_level,
        source_url=source_url,
        publisher=publisher,
        publication_date=publication_date,
        checksum=checksum,
        status="pending",
        uploaded_by=admin_user.id,
        tenant_id=admin_user.tenant_id,
    )
    db.add(doc)
    db.commit()
    
    background_tasks.add_task(
        process_document_ingestion,
        file_path=file_path,
        doc_id=file_id,
        department=department,
        language=language,
        version=version,
        title=doc_title,
        category=category,
        source_type=source_type,
        authority_level=authority_level,
        source_url=source_url,
        publisher=publisher,
        publication_date=publication_date,
        auto_activate=False,
        tenant_id=admin_user.tenant_id
    )
    
    return {"message": "Upload successful. Ingestion started.", "id": file_id, "checksum": checksum}

@router.get("/documents")
def list_documents(db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin", "super_admin"))):
    """List documents scoped to the admin's own tenant. super_admins see all."""
    query = db.query(DocumentMetadata).order_by(DocumentMetadata.uploaded_at.desc())
    if admin_user.role != "super_admin" and admin_user.tenant_id:
        query = query.filter(DocumentMetadata.tenant_id == admin_user.tenant_id)
    return query.all()

@router.get("/documents/{id}/status", response_model=DocumentStatusResponse)
def get_document_status(id: str, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin", "super_admin"))):
    query = db.query(DocumentMetadata).filter(DocumentMetadata.id == id)
    if admin_user.role != "super_admin" and admin_user.tenant_id:
        query = query.filter(DocumentMetadata.tenant_id == admin_user.tenant_id)
    doc = query.first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(id=doc.id, status=doc.status, filename=doc.filename)


@router.patch("/documents/{id}")
def update_document(id: str, req: UpdateDocRequest, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin", "super_admin"))):
    query = db.query(DocumentMetadata).filter(DocumentMetadata.id == id)
    if admin_user.role != "super_admin" and admin_user.tenant_id:
        query = query.filter(DocumentMetadata.tenant_id == admin_user.tenant_id)
    doc = query.first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if req.status in ['approved', 'active']:
        doc.status = 'active'
        # Archive older active versions of the same title and department (within tenant)
        older_query = db.query(DocumentMetadata).filter(
            DocumentMetadata.title == doc.title,
            DocumentMetadata.department == doc.department,
            DocumentMetadata.id != id,
            DocumentMetadata.status == 'active'
        )
        if admin_user.role != "super_admin" and admin_user.tenant_id:
            older_query = older_query.filter(DocumentMetadata.tenant_id == admin_user.tenant_id)
        for old_doc in older_query.all():
            old_doc.status = 'archived'
            archive_document_chunks(old_doc.id)

    elif req.status in ['archived', 'superseded']:
        doc.status = 'archived'
        archive_document_chunks(id)
    else:
        raise HTTPException(status_code=400, detail="Invalid status")

    db.commit()
    return {"status": "success", "new_status": doc.status}

@router.delete("/documents/{id}")
def delete_document(id: str, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin", "super_admin"))):
    query = db.query(DocumentMetadata).filter(DocumentMetadata.id == id)
    if admin_user.role != "super_admin" and admin_user.tenant_id:
        query = query.filter(DocumentMetadata.tenant_id == admin_user.tenant_id)
    doc = query.first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(id)
    db.delete(doc)
    db.commit()
    return {"status": "success"}

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin", "super_admin"))):
    """Returns analytics scoped to admin's tenant (super_admins see global stats)."""
    is_super = admin_user.role == "super_admin"
    tid = admin_user.tenant_id

    if not is_super and tid:
        total_messages = db.query(func.count(Message.id)).join(Conversation, Message.conversation_id == Conversation.id).filter(Conversation.tenant_id == tid).scalar()
        total_conversations = db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tid).scalar()
        total_users = db.query(func.count(User.id)).filter(User.tenant_id == tid).scalar()
        total_docs = db.query(func.count(DocumentMetadata.id)).filter(DocumentMetadata.tenant_id == tid).scalar()
        fallback_count = db.query(func.count(Message.id)).join(Conversation, Message.conversation_id == Conversation.id).filter(
            Conversation.tenant_id == tid, Message.is_fallback == True
        ).scalar()
    else:
        total_messages = db.query(func.count(Message.id)).scalar()
        total_conversations = db.query(func.count(Conversation.id)).scalar()
        total_users = db.query(func.count(User.id)).scalar()
        total_docs = db.query(func.count(DocumentMetadata.id)).scalar()
        fallback_count = db.query(func.count(Message.id)).filter(Message.is_fallback == True).scalar()

    fallback_rate = round(fallback_count / total_messages, 4) if total_messages > 0 else 0.0

    return {
        "total_messages": total_messages,
        "total_conversations": total_conversations,
        "total_users": total_users,
        "total_documents": total_docs,
        "fallback_rate": fallback_rate,
        "tenant_id": tid if not is_super else "global",
    }

@router.get("/unanswered-queries")
def get_unanswered_queries(db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin", "super_admin"))):
    query = db.query(Message).filter(Message.is_fallback == True, Message.role == 'assistant')
    if admin_user.role != "super_admin" and admin_user.tenant_id:
        query = query.join(Conversation, Message.conversation_id == Conversation.id).filter(
            Conversation.tenant_id == admin_user.tenant_id
        )
    queries = query.order_by(Message.created_at.desc()).limit(50).all()
    results = []
    for q in queries:
        user_msg = db.query(Message).filter(
            Message.conversation_id == q.conversation_id,
            Message.role == 'user',
            Message.created_at < q.created_at
        ).order_by(Message.created_at.desc()).first()
        if user_msg:
            results.append({
                "id": q.id,
                "user_query": user_msg.content,
                "timestamp": q.created_at
            })
    return results

@router.patch("/unanswered-queries/{id}")
def update_unanswered_query(id: str, req: ActionRequest, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin", "super_admin"))):
    if req.action not in ['needs_document', 'dismiss']:
        raise HTTPException(status_code=400, detail="Invalid action")
    return {"status": "success"}


# ─── Phase 12: Performance Metrics + User Management ─────────────────────────

@router.get("/metrics")
def get_performance_metrics(admin_user: User = Depends(require_role("admin", "super_admin"))):
    """
    Returns P50 / P95 / P99 latency percentiles for each RAG pipeline stage.
    Sourced from the in-process ring-buffer (last 1000 requests).
    """
    from backend.rag.engine import get_latency_percentiles
    return {
        "latency_percentiles": get_latency_percentiles(),
        "description": "All values are in milliseconds (ms). Based on last ≤1000 requests.",
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin", "super_admin")),
):
    """List all users in the admin's tenant (super_admin sees all)."""
    query = db.query(User)
    if admin_user.role != "super_admin" and admin_user.tenant_id:
        query = query.filter(User.tenant_id == admin_user.tenant_id)
    users = query.order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "tenant_id": u.tenant_id,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    body: UpdateDocRequest,  # reuse {status: str} pattern — field name is role value
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin", "super_admin")),
):
    """
    Change a user's role. Admins can promote students to admin within their tenant.
    Only super_admins can grant the super_admin role.
    """
    allowed_roles = {"student", "member", "viewer", "admin"}
    if admin_user.role == "super_admin":
        allowed_roles.add("super_admin")

    new_role = body.status  # reuse the status field as role value
    if new_role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role '{new_role}'. Allowed: {sorted(allowed_roles)}")

    query = db.query(User).filter(User.id == user_id)
    if admin_user.role != "super_admin" and admin_user.tenant_id:
        query = query.filter(User.tenant_id == admin_user.tenant_id)

    target_user = query.first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    target_user.role = new_role
    db.commit()

    log_audit_event(
        event_type="USER_ROLE_CHANGED",
        actor_id=admin_user.id,
        tenant_id=admin_user.tenant_id,
        action="update_role",
        status="SUCCESS",
        details={"target_user_id": user_id, "new_role": new_role}
    )

    return {"status": "success", "user_id": user_id, "new_role": new_role}


@router.get("/audit-logs")
def get_admin_audit_logs(
    limit: int = 50,
    admin_user: User = Depends(require_role("admin", "super_admin"))
):
    """Returns recent structured audit events scoped to tenant (super_admin sees all)."""
    tenant_scope = admin_user.tenant_id if admin_user.role != "super_admin" else "global"
    return {"audit_logs": get_audit_logs(tenant_id=tenant_scope, limit=limit)}

