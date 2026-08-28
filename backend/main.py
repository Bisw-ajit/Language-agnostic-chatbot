from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.database import create_tables, seed_demo_users
from backend.auth.router import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.admin import router as admin_router

app = FastAPI(title="Language Agnostic Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_tables()
    seed_demo_users()

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0"}
