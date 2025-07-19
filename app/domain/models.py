import uuid
import enum
from sqlalchemy import Column, String, DateTime, func, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class TaskStatusEnum(str, enum.Enum):
    pendiente = "pendiente"
    completado = "completado"
    detenido = "detenido"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    nombre_tarea = Column(String, nullable=False)
    descripcion_tarea = Column(String, nullable=True)
    fecha_completado_tarea = Column(DateTime, nullable=True)
    estado_tarea = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.pendiente, nullable=False)
    fecha_limite_tarea = Column(DateTime, nullable=True)
    id_referencia = Column(String, nullable=True)

    fecha_creacion_tarea = Column(DateTime, server_default=func.now())
    fecha_modificacion_tarea = Column(DateTime, server_default=func.now(), onupdate=func.now())

