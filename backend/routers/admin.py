import os
import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from backend.models.database import get_db, DocumentMetadata, Message, Conversation, User
from backend.auth.jwt import require_role
from backend.rag.ingestion import process_document_ingestion
from backend.rag.vector_store import delete_document_chunks, archive_document_chunks
from backend.contracts.api_types import DocumentMetadataResponse, DocumentStatusResponse

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

UPLOAD_DIR = "./uploads"
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
    admin_user: User = Depends(require_role("admin"))
):
    content = await file.read()
    checksum = hashlib.sha256(content).hexdigest()

    # Duplicate check on checksum
    existing_dup = db.query(DocumentMetadata).filter(
        DocumentMetadata.checksum == checksum,
        DocumentMetadata.status.in_(["active", "pending_approval", "pending"])
    ).first()
    if existing_dup:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate document detected (matches '{existing_dup.title}' v{existing_dup.version})"
        )

    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
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
        uploaded_by=admin_user.id
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
        auto_activate=False
    )
    
    return {"message": "Upload successful. Ingestion started.", "id": file_id, "checksum": checksum}

@router.get("/documents")
def list_documents(db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    docs = db.query(DocumentMetadata).order_by(DocumentMetadata.uploaded_at.desc()).all()
    return docs

@router.get("/documents/{id}/status", response_model=DocumentStatusResponse)
def get_document_status(id: str, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(id=doc.id, status=doc.status, filename=doc.filename)

@router.patch("/documents/{id}")
def update_document(id: str, req: UpdateDocRequest, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if req.status in ['approved', 'active']:
        doc.status = 'active'
        # Archive older active versions of the same title and department
        older_docs = db.query(DocumentMetadata).filter(
            DocumentMetadata.title == doc.title,
            DocumentMetadata.department == doc.department,
            DocumentMetadata.id != id,
            DocumentMetadata.status == 'active'
        ).all()
        for old_doc in older_docs:
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
def delete_document(id: str, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    delete_document_chunks(id)
    db.delete(doc)
    db.commit()
    return {"status": "success"}

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    total_messages = db.query(func.count(Message.id)).scalar()
    total_conversations = db.query(func.count(Conversation.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    total_docs = db.query(func.count(DocumentMetadata.id)).scalar()
    fallback_count = db.query(func.count(Message.id)).filter(Message.is_fallback == True).scalar()
    
    fallback_rate = 0.0
    if total_messages > 0:
        fallback_rate = fallback_count / total_messages
        
    return {
        "total_messages": total_messages,
        "total_conversations": total_conversations,
        "total_users": total_users,
        "total_documents": total_docs,
        "fallback_rate": fallback_rate
    }

@router.get("/unanswered-queries")
def get_unanswered_queries(db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    queries = db.query(Message).filter(Message.is_fallback == True, Message.role == 'assistant').order_by(Message.created_at.desc()).limit(50).all()
    # We should return the user message that caused the fallback
    results = []
    for q in queries:
        user_msg = db.query(Message).filter(Message.conversation_id == q.conversation_id, Message.role == 'user', Message.created_at < q.created_at).order_by(Message.created_at.desc()).first()
        if user_msg:
            results.append({
                "id": q.id,
                "user_query": user_msg.content,
                "timestamp": q.created_at
            })
    return results

@router.patch("/unanswered-queries/{id}")
def update_unanswered_query(id: str, req: ActionRequest, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    if req.action not in ['needs_document', 'dismiss']:
        raise HTTPException(status_code=400, detail="Invalid action")
    return {"status": "success"}
