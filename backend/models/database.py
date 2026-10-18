import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, Integer, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from passlib.context import CryptContext

from backend.config import get_settings

logger = logging.getLogger("database")
settings = get_settings()

# Engine configuration with connection pooling for PostgreSQL
if settings.postgres_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(settings.postgres_url, connect_args=connect_args)
else:
    engine = create_engine(
        settings.postgres_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800
    )

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

def get_utc_now():
    return datetime.now(timezone.utc)

class Organization(Base):
    """
    Multi-tenant organization boundary.
    All users, documents, conversations, and analytics are scoped to a tenant.
    """
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

    users = relationship("User", back_populates="organization")
    documents = relationship("DocumentMetadata", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("organizations.id"), nullable=True, default="default-tenant", index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False) # 'student' | 'admin' | 'super_admin' | 'member' | 'viewer'
    created_at = Column(DateTime, default=get_utc_now)

    organization = relationship("Organization", back_populates="users")
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("organizations.id"), nullable=True, default="default-tenant", index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    detected_language = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    is_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship("Feedback", uselist=False, back_populates="message", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(String, primary_key=True, default=generate_uuid)
    message_id = Column(String, ForeignKey("messages.id"), unique=True, nullable=False)
    rating = Column(String, nullable=False) # 'up' or 'down'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    message = relationship("Message", back_populates="feedback")

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("organizations.id"), nullable=True, default="default-tenant", index=True)
    title = Column(String, nullable=False, default="Untitled Document")
    description = Column(Text, nullable=True)
    filename = Column(String, nullable=False)
    department = Column(String, nullable=False)
    category = Column(String, default="Scheme", nullable=False)
    language = Column(String, default="en", nullable=False)
    source_type = Column(String, default="official", nullable=False)
    authority_level = Column(String, default="official", nullable=False)
    source_url = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    publication_date = Column(String, nullable=True)
    last_updated = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    version = Column(String, default="1.0", nullable=False)
    status = Column(String, default="pending", nullable=False)
    checksum = Column(String, index=True, nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=get_utc_now)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    organization = relationship("Organization", back_populates="documents")

class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("organizations.id"), nullable=True, default="default-tenant", index=True)
    date = Column(DateTime, default=get_utc_now, unique=True)
    total_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    fallback_count = Column(Integer, default=0)

def create_tables():
    Base.metadata.create_all(bind=engine)

def seed_demo_users():
    db = SessionLocal()
    try:
        # Seed default organization
        default_org = db.query(Organization).filter(Organization.id == "default-tenant").first()
        if not default_org:
            default_org = Organization(
                id="default-tenant",
                name="Odisha State Administration",
                slug="odisha-gov"
            )
            db.add(default_org)
            db.commit()

        student = db.query(User).filter(User.email == "student@demo.com").first()
        if not student:
            student = User(
                email="student@demo.com",
                hashed_password=pwd_context.hash("demo123"),
                role="student",
                tenant_id="default-tenant"
            )
            db.add(student)
            
        admin = db.query(User).filter(User.email == "admin@demo.com").first()
        if not admin:
            admin = User(
                email="admin@demo.com",
                hashed_password=pwd_context.hash("admin123"),
                role="admin",
                tenant_id="default-tenant"
            )
            db.add(admin)
        db.commit()
    finally:
        db.close()
