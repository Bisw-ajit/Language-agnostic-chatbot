import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.models.database import get_db, Conversation, Message, Feedback, User
from backend.auth.jwt import get_current_user
from backend.contracts.api_types import ChatRequest, ChatResponse, Source, FeedbackRequest
from backend.rag.engine import get_rag_engine
from backend.rag.injection_guard import sanitize_query, get_injection_rejection_message
from backend.observability import (
    record_rag_query,
    record_injection_block,
    record_evidence_validation,
    log_audit_event
)

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation_id = request.conversation_id
    
    user_tenant = current_user.tenant_id or "default-tenant"
    if not conversation_id:
        new_conv = Conversation(user_id=current_user.id, tenant_id=user_tenant)
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conversation_id = new_conv.id
    else:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
            Conversation.tenant_id == user_tenant
        ).first()
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
    
    # ── Phase 15: Prompt Injection Guard ─────────────────────────────────────
    is_safe, sanitized_message, threat_label = sanitize_query(request.message)
    if not is_safe:
        # Record security metrics and audit event
        record_injection_block(threat_label=threat_label)
        log_audit_event(
            event_type="PROMPT_INJECTION_BLOCKED",
            actor_id=current_user.id,
            tenant_id=user_tenant,
            action="query_sanitization",
            status="BLOCKED",
            details={"threat_label": threat_label, "query_preview": request.message[:120]}
        )

        # Return a deterministic rejection — do NOT invoke the LLM
        rejection_text = get_injection_rejection_message(threat_label)
        rejected_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=rejection_text,
            detected_language="en",
            confidence_score=1.0,
            is_fallback=True,
        )
        db.add(rejected_msg)
        db.commit()
        db.refresh(rejected_msg)
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=rejected_msg.id,
            answer=rejection_text,
            sources=[],
            detected_language="en",
            language_display="English",
            confidence=1.0,
            evidence_level="BLOCKED",
            is_fallback=True,
            llm_status="BLOCKED_INJECTION",
            generation_source="injection_guard",
        )

    # Execute modular RAG engine pipeline
    engine = get_rag_engine()
    rag_result = engine.process_query(
        query=request.message,
        conversation_history=history,
        preferred_language=request.preferred_language,
        tenant_id=user_tenant,
    )

    # Record RAG query metrics & validation outcome
    record_rag_query(
        language=rag_result.get("detected_language", "en"),
        is_fallback=rag_result.get("is_fallback", False)
    )
    record_evidence_validation(passed=not rag_result.get("is_fallback", False))
    
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
        llm_status=rag_result.get("llm_status", "LLM_SUCCESS"),
        generation_source=rag_result.get("generation_source", "gemini"),
        rewritten_query=rag_result.get("rewritten_query"),
        latency_ms=rag_result.get("latency_ms"),
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


# ─── Phase 10: Server-Sent Events Streaming Endpoint ─────────────────────────

@router.post("/chat/stream", tags=["chat"])
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    Event types emitted:
      - ``status``  : pipeline stage notifications (retrieval, generating)
      - ``token``   : individual answer tokens streamed word-by-word
      - ``sources`` : JSON array of evidence sources (after answer completes)
      - ``meta``    : final metadata (language, confidence, latency_ms, llm_status)
      - ``done``    : signals end of stream
      - ``error``   : fatal error payload
    """
    conversation_id = request.conversation_id
    user_tenant = current_user.tenant_id or "default-tenant"

    if not conversation_id:
        new_conv = Conversation(user_id=current_user.id, tenant_id=user_tenant)
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conversation_id = new_conv.id
    else:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
            Conversation.tenant_id == user_tenant,
        ).first()
        if not conv:
            async def _err():
                yield f"event: error\ndata: {json.dumps({'detail': 'Conversation not found'})}\n\n"
            return StreamingResponse(_err(), media_type="text/event-stream")

    # ── Prompt Injection Defense for Streaming ──────────────────────────────
    is_safe, sanitized_message, threat_label = sanitize_query(request.message)
    if not is_safe:
        record_injection_block(threat_label=threat_label)
        log_audit_event(
            event_type="PROMPT_INJECTION_BLOCKED",
            actor_id=current_user.id,
            tenant_id=user_tenant,
            action="query_sanitization_stream",
            status="BLOCKED",
            details={"threat_label": threat_label, "query_preview": request.message[:120]}
        )
        rejection_text = get_injection_rejection_message(threat_label)
        rejected_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=rejection_text,
            detected_language="en",
            confidence_score=1.0,
            is_fallback=True,
        )
        db.add(rejected_msg)
        db.commit()
        db.refresh(rejected_msg)

        async def _blocked_stream():
            yield f"event: status\ndata: {json.dumps({'stage': 'blocked', 'threat': threat_label})}\n\n"
            yield f"event: token\ndata: {json.dumps({'token': rejection_text})}\n\n"
            meta = {
                "message_id": rejected_msg.id,
                "conversation_id": conversation_id,
                "detected_language": "en",
                "language_display": "English",
                "confidence": 1.0,
                "evidence_level": "BLOCKED",
                "is_fallback": True,
                "llm_status": "BLOCKED_INJECTION",
                "generation_source": "injection_guard",
            }
            yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(_blocked_stream(), media_type="text/event-stream")

    user_msg = Message(conversation_id=conversation_id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    history_msgs = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]

    _conv_id = conversation_id
    _tenant = user_tenant
    _query = sanitized_message
    _lang = request.preferred_language

    async def event_generator():
        try:
            yield f"event: status\ndata: {json.dumps({'stage': 'retrieval', 'conversation_id': _conv_id})}\n\n"
            await asyncio.sleep(0)

            loop = asyncio.get_event_loop()
            engine = get_rag_engine()
            rag_result = await loop.run_in_executor(
                None,
                lambda: engine.process_query(
                    query=_query,
                    conversation_history=history,
                    preferred_language=_lang,
                    tenant_id=_tenant,
                ),
            )

            yield f"event: status\ndata: {json.dumps({'stage': 'generating'})}\n\n"
            await asyncio.sleep(0)

            answer: str = rag_result.get("answer", "")
            words = answer.split(" ")
            for i, word in enumerate(words):
                token = word if i == 0 else " " + word
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0.01)

            asst_msg = Message(
                conversation_id=_conv_id,
                role="assistant",
                content=answer,
                detected_language=rag_result.get("detected_language", "en"),
                confidence_score=rag_result.get("confidence", 0.0),
                is_fallback=rag_result.get("is_fallback", False),
            )
            db.add(asst_msg)
            db.commit()
            db.refresh(asst_msg)

            sources_payload = [
                {
                    "document_id": str(s.get("document_id", "")),
                    "document_title": str(s.get("document_title", s.get("title", "Document"))),
                    "section": str(s.get("section", "General")),
                    "score": float(s.get("score", 0.0)),
                    "excerpt": str(s.get("text", ""))[:220],
                }
                for s in rag_result.get("sources", [])
            ]
            yield f"event: sources\ndata: {json.dumps(sources_payload)}\n\n"
            await asyncio.sleep(0)

            meta = {
                "message_id": asst_msg.id,
                "conversation_id": _conv_id,
                "detected_language": rag_result.get("detected_language", "en"),
                "language_display": rag_result.get("language_display", "English"),
                "confidence": rag_result.get("confidence", 0.0),
                "evidence_level": rag_result.get("evidence_level", "HIGH"),
                "is_fallback": rag_result.get("is_fallback", False),
                "llm_status": rag_result.get("llm_status", "LLM_SUCCESS"),
                "generation_source": rag_result.get("generation_source", "gemini"),
                "latency_ms": rag_result.get("latency_ms"),
            }
            yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
            yield "event: done\ndata: {}\n\n"

        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
