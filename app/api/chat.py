import datetime

from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.schemas import ChatRequest, ChatResponse, APIResponse
from app.core.redis import get_redis
from app.core.database import get_db
from app.services.auth_services import get_current_user_id
from app.services.chat_services import get_intent_prompt, get_response

router = APIRouter()

@router.post("/", response_model=APIResponse[ChatResponse], status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    redis = Depends(get_redis),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        mess, data, status = await get_response(request, redis, db, user_id)
        
        if status == "incomplete":
            return APIResponse(
                message=mess,
                data=data,
                status=status
            )

        return APIResponse(
            message=mess,
            data=data,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
