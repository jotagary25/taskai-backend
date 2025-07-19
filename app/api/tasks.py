from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.schemas import TaskCreate, TaskUpdate, TaskRead, APIResponse
from app.domain.models import Task, TaskStatusEnum
from app.core.database import get_db
from app.services.auth_services import get_current_user_id

router = APIRouter()

@router.post("/", response_model=APIResponse[TaskCreate], status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    try:
      task = Task(
          id_usuario=user_id,
          nombre_tarea=task_in.nombre_tarea,
          descripcion_tarea=task_in.descripcion_tarea,
          fecha_limite_tarea=task_in.fecha_limite_tarea,
          estado_tarea=TaskStatusEnum.pendiente,
      )
      db.add(task)
      db.commit()
      db.refresh(task)
      return APIResponse(
          message="tarea creada exitosamente",
          data=task,
          status="success"
      )
    except IntegrityError as e:
      raise HTTPException(status_code=400, detail=f'error de integridad: {str(e)}')
    except Exception as e:
      raise HTTPException(status_code=500, detail=f'error de servidor: {str(e)}')

@router.get("/", response_model=APIResponse[list[TaskRead]], status_code=status.HTTP_200_OK)
def get_tasks(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        tasks = db.query(Task).filter(Task.id_usuario == user_id).all()
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
        task = db.query(Task).filter(Task.id == task_id, Task.id_usuario == user_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        for var, value in vars(task_update).items():
            if value is not None:
                setattr(task, var, value)
        db.commit()
        db.refresh(task)
        return APIResponse(
            message="tarea actualizada exitosamente",
            data=task,
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
        task = db.query(Task).filter(Task.id == task_id, Task.id_usuario == user_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        db.delete(task)
        db.commit()
        return APIResponse(
            message="tarea eliminada exitosamente",
            data=None,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
