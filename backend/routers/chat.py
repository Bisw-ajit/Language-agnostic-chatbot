from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db, Conversation, Message, Feedback, User
from backend.auth.jwt import get_current_user
from backend.contracts.api_types import ChatRequest, ChatResponse, Source, FeedbackRequest
from backend.rag.engine import get_rag_engine

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation_id = request.conversation_id
    
    if not conversation_id:
        new_conv = Conversation(user_id=current_user.id)
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conversation_id = new_conv.id
    else:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Save original user message unmodified
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    db.commit()
    
    # Fetch recent conversation history
    history_msgs = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]
    
    # Execute modular RAG engine pipeline
    engine = get_rag_engine()
    rag_result = engine.process_query(
        query=request.message,
        conversation_history=history,
        preferred_language=request.preferred_language
    )
    
    # Save assistant message with language, confidence, and fallback telemetry
    asst_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=rag_result["answer"],
        detected_language=rag_result["detected_language"],
        confidence_score=rag_result["confidence"],
        is_fallback=rag_result["is_fallback"]
    )
    db.add(asst_msg)
    db.commit()
    db.refresh(asst_msg)
    
    formatted_sources = [
        Source(
            document_id=str(s.get("document_id", "")),
            source=str(s.get("source", "Official Document")),
            document_title=str(s.get("document_title", s.get("title", s.get("source", "Official Document")))),
            title=str(s.get("title", s.get("document_title", "Document"))),
            page=int(s.get("page", 1)),
            section=str(s.get("section", "General")),
            department=str(s.get("department", "General")),
            category=str(s.get("category", "Scheme")),
            language=str(s.get("language", "en")),
            version=str(s.get("version", "1.0")),
            source_type=str(s.get("source_type", "official")),
            authority_level=str(s.get("authority_level", "official")),
            source_url=s.get("source_url"),
            publication_date=s.get("publication_date"),
            last_updated=s.get("last_updated"),
            excerpt=str(s.get("excerpt", s.get("text", "")[:220])),
            score=float(s.get("score", 0.0))
        ) for s in rag_result["sources"]
    ]
    
    return ChatResponse(
        conversation_id=conversation_id,
        message_id=asst_msg.id,
        answer=rag_result["answer"],
        sources=formatted_sources,
        detected_language=rag_result["detected_language"],
        language_display=rag_result["language_display"],
        script=rag_result.get("script", "latin"),
        confidence=rag_result["confidence"],
        evidence_level=rag_result.get("evidence_level", "HIGH"),
        conflicts=rag_result.get("conflicts", []),
        is_fallback=rag_result["is_fallback"],
        rewritten_query=rag_result.get("rewritten_query")
    )

@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    convs = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc()).all()
    result = []
    for c in convs:
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()
        result.append({
            "id": c.id,
            "last_message": last_msg.content if last_msg else "New Conversation",
            "updated_at": c.updated_at
        })
    return result

@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "detected_language": m.detected_language,
            "confidence_score": m.confidence_score,
            "is_fallback": m.is_fallback,
            "created_at": m.created_at
        }
        for m in messages
    ]

@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(conv)
    db.commit()
    return {"status": "success", "message": "Conversation deleted"}

@router.post("/feedback")
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = db.query(Message).filter(Message.id == request.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    conv = db.query(Conversation).filter(Conversation.id == msg.conversation_id).first()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    feedback = db.query(Feedback).filter(Feedback.message_id == request.message_id).first()
    if feedback:
        feedback.rating = request.rating
        feedback.comment = request.comment
    else:
        feedback = Feedback(message_id=request.message_id, rating=request.rating, comment=request.comment)
        db.add(feedback)
        
    db.commit()
    return {"status": "success"}

