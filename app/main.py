from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.domain.models import Base
from app.core.database import engine
from app.api import auth
from app.api import chat

app = FastAPI(
    title="TASK AI",
    description="API para agendar y consultar tareas con LLM",
    version="0.1.0"
)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
async def health_check():
    return {"message": "Backend funcionando correctamente!"}