import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.models.database import get_db, User, pwd_context
from backend.auth.jwt import create_access_token, get_current_user, require_role
from backend.contracts.api_types import LoginResponse, RegisterRequest

logger = logging.getLogger("chatbot.auth.router")
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register")
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    clean_email = user_data.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid email address is required")
    if len(user_data.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")

    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user_data.password)
    # SECURITY GATE: Public registration strictly forces "student" role.
    # Client-submitted role parameters are completely ignored to prevent privilege escalation.
    new_user = User(
        email=clean_email,
        hashed_password=hashed_password,
        role="student"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "role": "student"}

@router.post("/create-admin")
def create_admin(
    user_data: RegisterRequest, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(require_role("admin", "super_admin"))
):
    """Protected admin provisioning: requires authenticated administrator session."""
    clean_email = user_data.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid email address is required")
    if len(user_data.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")

    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = pwd_context.hash(user_data.password)
    new_admin = User(
        email=clean_email,
        hashed_password=hashed_password,
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"message": "Administrator account provisioned successfully", "user_id": new_admin.id}

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    username = None
    password = None
    
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username") or body.get("email")
            password = body.get("password")
        except Exception as exc:
            logger.debug("Failed to parse JSON login body: %s", exc)
    else:
        try:
            form = await request.form()
            username = form.get("username") or form.get("email")
            password = form.get("password")
        except Exception as exc:
            logger.debug("Failed to parse form login body: %s", exc)

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    user = db.query(User).filter(User.email == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        tenant_id=user.tenant_id or "default-tenant",
        email=user.email
    )

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id or "default-tenant"
    }
