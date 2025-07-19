from fastapi import APIRouter, Depends, HTTPException,status
from app.api.schemas import ChatRequest, ChatResponse, APIResponse
from app.core.redis import get_redis
from app.services.context_services import RedisContextService
from app.services.auth_services import get_current_user_id

import datetime

router = APIRouter()

@router.post("/", response_model=APIResponse[ChatResponse], status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    redis = Depends(get_redis),
    user_id: str = Depends(get_current_user_id),
):
    try:
        context_service = RedisContextService(redis)
        await context_service.push_message(user_id, {
            "role": "user",
            "content": request.user_input,
            "timestamp": datetime.datetime.now().isoformat()
        })
        context = await context_service.get_context(user_id)
        response = f"contexto actual ({len(context)} mensajes): {[m['content'] for m in context]}"
        await context_service.push_message(user_id, {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.datetime.now().isoformat()
        })
        return APIResponse(
            message="respuesta generada exitosamente",
            data=ChatResponse(response=response),
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
