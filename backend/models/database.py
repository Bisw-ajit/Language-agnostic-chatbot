import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, Integer, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from passlib.context import CryptContext
from backend.config import get_settings

settings = get_settings()
engine = create_engine(settings.postgres_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    detected_language = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    is_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship("Feedback", uselist=False, back_populates="message")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(String, primary_key=True, default=generate_uuid)
    message_id = Column(String, ForeignKey("messages.id"), unique=True, nullable=False)
    rating = Column(String, nullable=False) # 'up' or 'down'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="feedback")

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    department = Column(String, nullable=False)
    language = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"
    id = Column(String, primary_key=True, default=generate_uuid)
    date = Column(DateTime, default=datetime.utcnow, unique=True)
    total_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    fallback_count = Column(Integer, default=0)

def create_tables():
    Base.metadata.create_all(bind=engine)

def seed_demo_users():
    db = SessionLocal()
    try:
        student = db.query(User).filter(User.email == "student@demo.com").first()
        if not student:
            student = User(
                email="student@demo.com",
                hashed_password=pwd_context.hash("demo123"),
                role="student"
            )
            db.add(student)
            
        admin = db.query(User).filter(User.email == "admin@demo.com").first()
        if not admin:
            admin = User(
                email="admin@demo.com",
                hashed_password=pwd_context.hash("admin123"),
                role="admin"
            )
            db.add(admin)
        db.commit()
    finally:
        db.close()
