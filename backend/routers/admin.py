import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from backend.models.database import get_db, DocumentMetadata, Message, Conversation, User
from backend.auth.jwt import require_role
from backend.ingestion.pipeline import run_ingestion_pipeline
from backend.retrieval.retriever import get_chroma_client
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
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin"))
):
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    doc = DocumentMetadata(
        id=file_id,
        filename=file.filename,
        department=department,
        language=language,
        version=version,
        status="pending",
        uploaded_by=admin_user.id
    )
    db.add(doc)
    db.commit()
    
    background_tasks.add_task(run_ingestion_pipeline, file_path, file_id, department, language, version)
    
    return {"message": "Upload successful. Ingestion started.", "id": file_id}

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
        
    if req.status == 'approved':
        if doc.status == 'pending_approval':
            # It's already in ChromaDB. We just mark it as indexed.
            doc.status = 'indexed'
        else:
            raise HTTPException(status_code=400, detail=f"Cannot approve document in {doc.status} state")
            
    elif req.status == 'superseded':
        doc.status = 'superseded'
        try:
            collection = get_chroma_client().get_collection(name='documents')
            collection.delete(where={"document_id": id})
        except Exception as e:
            print(f"Error deleting from chroma: {e}")
    else:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    db.commit()
    return {"status": "success", "new_status": doc.status}

@router.delete("/documents/{id}")
def delete_document(id: str, db: Session = Depends(get_db), admin_user: User = Depends(require_role("admin"))):
    doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        collection = get_chroma_client().get_collection(name='documents')
        collection.delete(where={"document_id": id})
    except Exception as e:
        print(f"Error deleting from chroma: {e}")
        
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
