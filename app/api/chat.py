from fastapi import APIRouter
from app.api.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return ChatResponse(response=f"recibido: {request.user_input}")