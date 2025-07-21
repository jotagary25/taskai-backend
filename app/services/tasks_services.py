from psycopg2 import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from app.api.schemas import TaskStatusEnum as TaskStatusEnumSchema, TaskUpdate, TaskCreate
from app.domain.models import Task, TaskStatusEnum as TaskStatusEnumModel
from datetime import datetime

def create_task_service(task_in: TaskCreate, db:Session, user_id: UUID):
    try:
        task = Task(
            id_usuario=user_id,
            nombre_tarea=task_in.nombre_tarea,
            descripcion_tarea=task_in.descripcion_tarea,
            fecha_limite_tarea=task_in.fecha_limite_tarea,
            estado_tarea=TaskStatusEnumModel.pendiente,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    except IntegrityError as e:
        print(f"Integrity error: {str(e)}")
        return None
    except Exception as e:
        print(f"Server error: {str(e)}")
        return None

def get_tasks_for_user_service(
    db: Session,
    user_id: UUID,
    estado_tarea: Optional[TaskStatusEnumSchema],
    fecha_desde: Optional[datetime],
    fecha_hasta: Optional[datetime],
):
    query = db.query(Task).filter(Task.id_usuario == user_id)
    if estado_tarea:
        query = query.filter(Task.estado_tarea == estado_tarea)
    if fecha_desde:
        query = query.filter(Task.fecha_limite_tarea >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Task.fecha_limite_tarea <= fecha_hasta)
    return query.all()

def update_task_service(task_id: int, task_update: TaskUpdate, db: Session, user_id: UUID):
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.id_usuario == user_id).first()
        if not Task:
            return None
        for var, value in vars(task_update).items():
            if value is not None:
                setattr(task, var, value)
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        print(f"Server error: {str(e)}")
        return None

def delete_task_service(task_id: int, user_id: UUID, db: Session):
    task = db.query(Task).filter(Task.id == task_id, Task.id_usuario == user_id).first()
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True

def get_next_task_service(user_id: UUID, db:Session):
    task = (
        db.query(Task)
        .filter(Task.id_usuario == user_id, Task.estado_tarea == TaskStatusEnumModel.pendiente)
        .order_by(Task.fecha_limite_tarea.asc())
        .first()
    )
    if not task:
        return None
    return task