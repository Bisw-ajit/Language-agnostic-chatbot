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
    page: int
    department: str
    language: str
    excerpt: str

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    sources: List[Source]
    detected_language: str
    language_display: str
    confidence: float
    is_fallback: bool

class FeedbackRequest(BaseModel):
    message_id: str
    rating: str # 'up' or 'down'
    comment: Optional[str] = None

class DocumentMetadataResponse(BaseModel):
    id: str
    filename: str
    department: str
    language: str
    version: str
    status: str
    uploaded_at: datetime
    uploaded_by: str

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
