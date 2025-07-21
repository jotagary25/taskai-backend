from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import datetime

from app.api.schemas import TaskCreate, TaskUpdate, TaskRead, APIResponse, TaskStatusEnum as TaskStatusEnumSchema
from app.domain.models import Task, TaskStatusEnum as TaskStatusEnumModel
from app.core.database import get_db
from app.services.auth_services import get_current_user_id
from app.services.tasks_services import (
    create_task_service,
    get_tasks_for_user_service, 
    get_next_task_service, 
    delete_task_service,
    update_task_service
)

router = APIRouter()

@router.post("/", response_model=APIResponse[TaskCreate], status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        response = create_task_service(task_in, db, user_id)
        if response is None:
            raise HTTPException(status_code=400, detail="Error al crear la tarea")
        return APIResponse(
            message="tarea creada exitosamente",
            data=response,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'error de servidor: {str(e)}')

@router.get("/", response_model=APIResponse[list[TaskRead]], status_code=status.HTTP_200_OK)
def get_tasks(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    estado: Optional[TaskStatusEnumSchema] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
):
    try:
        tasks = get_tasks_for_user_service(db, user_id, estado, fecha_desde, fecha_hasta)
        return APIResponse(
            message="tareas obtenidas exitosamente",
            data=tasks,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{task_id}", response_model=APIResponse[TaskRead], status_code=status.HTTP_200_OK)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        response = update_task_service(task_id, task_update, db, user_id)
        if not response:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        return APIResponse(
            message="tarea actualizada exitosamente",
            data=response,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}", response_model=APIResponse[None], status_code=status.HTTP_200_OK)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
        response = delete_task_service(task_id, user_id, db)
        if not response:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        return APIResponse(
            message="tarea eliminada exitosamente",
            data=None,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/next", response_model=APIResponse[TaskRead], status_code=status.HTTP_200_OK)
def get_next_task(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        response = get_next_task_service(user_id, db)
        if response is None:
            raise HTTPException(status_code=404, detail="No hay tareas pendientes")
        return APIResponse(
            message="tarea obtenida exitosamente",
            data=response,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))