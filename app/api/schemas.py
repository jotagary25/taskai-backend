from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from enum import Enum

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    message: str
    data: Optional[T] = None
    status: str = "success"

# SCHEMAS FOR TASKS
class TaskStatusEnum(str, Enum):
    pendiente = "pendiente"
    completado = "completado"
    detenido = "detenido"

class TaskCreate(BaseModel):
    nombre_tarea: str = Field(..., max_length=100)
    descripcion_tarea: Optional[str] = Field(None, max_length=500)
    fecha_limite_tarea: Optional[datetime] = None

class TaskUpdate(BaseModel):
    nombre_tarea: Optional[str] = Field(None, max_length=100)
    descripcion_tarea: Optional[str] = Field(None, max_length=500)
    fecha_limite_tarea: Optional[datetime] = None
    estado_tarea: Optional[TaskStatusEnum] = None

class TaskRead(BaseModel):
    id: int
    id_usuario: UUID
    nombre_tarea: str
    descripcion_tarea: Optional[str]
    fecha_completado_tarea: Optional[datetime]
    estado_tarea: TaskStatusEnum
    fecha_limite_tarea: Optional[datetime]
    id_referencia: Optional[str]
    fecha_creacion_tarea: datetime
    fecha_modificacion_tarea: datetime

    class Config:
        model_config = {"from_attributes": True}

# SCHEMAS FOR USER
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: UUID
    email: EmailStr

    class Config:
        model_config = {"from_attributes": True}

# SCHEMAS FOR AUTH
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# SCHEMAS FOR CHATS
class ChatRequest(BaseModel):
    user_input: str

class ChatResponse(BaseModel):
    response: str
