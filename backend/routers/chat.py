from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db, Conversation, Message, Feedback, User
from backend.auth.jwt import get_current_user
from backend.contracts.api_types import ChatRequest, ChatResponse, Source, FeedbackRequest
from backend.rag.chain import build_rag_response

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
    
    # Save user message
    user_msg = Message(conversation_id=conversation_id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()
    
    # Get history
    history_msgs = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]
    
    # Call RAG
    rag_result = build_rag_response(request.message, history)
    
    # Save assistant message
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
            document_id=s["document_id"],
            source=s["source"],
            page=s["page"],
            department=s["department"],
            language=s["language"],
            excerpt=s["excerpt"]
        ) for s in rag_result["sources"]
    ]
    
    return ChatResponse(
        conversation_id=conversation_id,
        message_id=asst_msg.id,
        answer=rag_result["answer"],
        sources=formatted_sources,
        detected_language=rag_result["detected_language"],
        language_display=rag_result["language_display"],
        confidence=rag_result["confidence"],
        is_fallback=rag_result["is_fallback"]
    )

@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    convs = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc()).all()
    result = []
    for c in convs:
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()
        result.append({
            "id": c.id,
            "last_message": last_msg.content if last_msg else "",
            "updated_at": c.updated_at
        })
    return result

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
