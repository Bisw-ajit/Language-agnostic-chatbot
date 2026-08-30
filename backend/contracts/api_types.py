from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "student"

class Source(BaseModel):
    document_id: str
    source: str
    document_title: Optional[str] = None
    title: Optional[str] = None
    page: int
    section: Optional[str] = "General"
    department: str
    category: Optional[str] = "Scheme"
    language: str
    version: Optional[str] = "1.0"
    source_type: Optional[str] = "official"
    authority_level: Optional[str] = "official"
    source_url: Optional[str] = None
    publication_date: Optional[str] = None
    last_updated: Optional[str] = None
    excerpt: str
    score: Optional[float] = 0.0

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    preferred_language: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    sources: List[Source]
    detected_language: str
    language_display: str
    script: Optional[str] = "latin"
    confidence: float
    evidence_level: Optional[str] = "HIGH"
    conflicts: Optional[List[str]] = None
    is_fallback: bool
    rewritten_query: Optional[str] = None

class FeedbackRequest(BaseModel):
    message_id: str
    rating: str # 'up' or 'down'
    comment: Optional[str] = None

class DocumentMetadataResponse(BaseModel):
    id: str
    title: Optional[str] = None
    filename: str
    department: str
    category: Optional[str] = "Scheme"
    language: str
    version: str
    source_type: Optional[str] = "official"
    authority_level: Optional[str] = "official"
    source_url: Optional[str] = None
    checksum: Optional[str] = None
    status: str
    uploaded_at: datetime

class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    filename: str

class ConversationSummary(BaseModel):
    id: str
    last_message: str
    updated_at: datetime

class AnalyticsResponse(BaseModel):
    total_messages: int
    total_conversations: int
    total_users: int
    total_documents: int
    fallback_rate: float
