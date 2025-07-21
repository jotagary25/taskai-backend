import json
import datetime as datetime_module

from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List

from app.services.llm_services import get_gemini_llm
from app.api.schemas import TaskCreate, ChatRequest, ChatResponse
from app.services.context_services import RedisContextService
from app.services.tasks_services import (
    create_task_service,
    get_tasks_for_user_service,
    update_task_service,
    delete_task_service,
    get_next_task_service
)

llm = get_gemini_llm()

async def get_response(request: ChatRequest, redis, db:Session, user_id_uuid: UUID):
    context_service = RedisContextService(redis)
    user_id = str(user_id_uuid)

    await context_service.push_message(user_id, {
        "role": "user",
        "content": request.user_input,
        "timestamp": datetime_module.datetime.now().isoformat()
    })
    
    PROMPT = get_intent_prompt(request.user_input)
    intent_response = llm.invoke(PROMPT)
    raw_intent = intent_response.content
    if isinstance(raw_intent, list):
        raw_intent = raw_intent[0] if raw_intent and isinstance(raw_intent[0], str) else "" 
    intent = raw_intent.strip().lower()
    print(f"[Intencion detectada]: {intent}")
    
    # detectar intenciones
    mess, content, status = await dispatch_by_intent(intent, request.user_input, user_id_uuid, db, context_service)
    
    # Si la intención falló, mostrar el error al usuario
    if status != "success":
        await context_service.push_message(user_id, {
            "role": "assistant",
            "content": content,
            "timestamp": datetime_module.datetime.now().isoformat()
        })
        return mess, ChatResponse(response=content), status

    # Si la intención fue completada con éxito, usar directamente la respuesta
    if status == "success" and content:
        await context_service.push_message(user_id, {
            "role": "assistant",
            "content": content,
            "timestamp": datetime_module.datetime.now().isoformat()
        })
        return "respuesta generada", ChatResponse(response=content), "success"

async def dispatch_by_intent(
    intent: str,
    user_input: str,
    user_id: UUID,
    db: Session,
    context_service,
):
    # --- Intenciones sin lógica de base de datos ---
    if intent == "greet":
        context = await context_service.get_context(str(user_id))
        response: str = await stylize_response(context, "saludar", "¡Hola! ¿En qué puedo ayudarte hoy?")
        return "intent_greet", response, "success"

    if intent == "goodbye":
        context = await context_service.get_context(str(user_id))
        response: str = await stylize_response(context, "Despedir", "¡Hasta luego! Que tengas un gran día.")
        return "intent_goodbye", response, "success"

    if intent == "smalltalk":
        context = await context_service.get_context(str(user_id))
        response: str = await stylize_response(context, "charlar", "Ok respondere a tu mensaje.")
        return "intent_smalltalk", response, "success"

    if intent == "clarification":
        return "intent_clarification", "Perdón si no me expresé bien. ¿Querés que te repita lo anterior o que lo aclare?", "success"

    if intent == "fallback":
        return "intent_fallback", "No entendí tu mensaje. ¿Podés reformularlo o preguntarme sobre tus tareas?", "success"

    if intent == "missing_info":
        return "intent_missing_info", "Necesito más datos para poder ayudarte. ¿Podés darme más detalles?", "success"

    # --- Intenciones con lógica de tareas ---
    if intent == "next_task":
        task = get_next_task_service(user_id, db)
        if not task:
            return "No tenés tareas pendientes por ahora."
        return f"Tu próxima tarea es: '{task.nombre_tarea}' para el {task.fecha_limite_tarea.strftime('%d/%m/%Y %H:%M')}."

    if intent == "list_tasks_today":
        today = datetime.now()
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end = today.replace(hour=23, minute=59, second=59)
        tasks = get_tasks_for_user_service(db, user_id, None, start, end)
        if not tasks:
            return "No tenés tareas programadas para hoy."
        return f"Estas son tus tareas para hoy:\n" + "\n".join(f"- {t.nombre_tarea}" for t in tasks)

    if intent == "list_tasks_week":
        today = datetime.now()
        start = today - timedelta(days=today.weekday())  # lunes
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        tasks = get_tasks_for_user_service(db, user_id, None, start, end)
        if not tasks:
            return "No hay tareas programadas para esta semana."
        return f"Estas son tus tareas de la semana:\n" + "\n".join(f"- {t.nombre_tarea} ({t.fecha_limite_tarea.strftime('%A')})" for t in tasks)

    if intent == "consult_tasks":
        context = await context_service.get_context(str(user_id))
        raw_json = build_date_range_prompt(context, user_input)
        print("[Respuesta de rango de fechas]:", raw_json)
        start, end = parse_date_range_response(raw_json)
        print("[Rango de fechas parseado]:", start, end)

        tasks = get_tasks_for_user_service(db, user_id, None, start, end)
        print("[Tareas encontradas]:", tasks)
        if not tasks:
            response_notasks = await stylize_response(context, "listar_tareas", "No tenés tareas pendientes.")
            return "sin_tareas", response_notasks, "success"
        
        msg = "Estas son tus tareas:\n" + "\n".join(
            f"- {t.nombre_tarea} ({t.fecha_limite_tarea.strftime('%d/%m %H:%M') if t.fecha_limite_tarea is not None else 'sin fecha'}), ¿Deseas cambiar las fechas?"
            for t in tasks
        )

        response_tasks = await stylize_response(context, "listar_tareas", msg)
        return "tareas_listadas", response_tasks, "success"

    if intent == "schedule_task":
        redis = context_service.redis
        user_id_str = str(user_id)

        # Paso 1: Recuperar contexto + draft
        context = await context_service.get_context(user_id_str)
        # para ver el contexto
        print(f"[Contexto recuperado para {user_id_str}]:")
        for i, mensaje in enumerate(context, 1):
            print(f"  {i}. {mensaje['role']}: {mensaje['content']}")

        draft_json = await redis.get(f"draft:schedule_task:{user_id_str}")

        # Paso 2: Generar prompt y obtener respuesta del LLM
        raw_json = build_fused_schedule_prompt(context, user_input, draft_json)

        task_fields = parse_task_fields_from_llm(raw_json)

        # Paso 3: Validación previa
        if not isinstance(task_fields, dict):
            print(f"[ERROR]: task_fields inválido o vacío: {task_fields}")
            return "error", "La respuesta del modelo no contiene una tarea válida.", "error"

        nombre = task_fields.get("nombre_tarea")
        descripcion = task_fields.get("descripcion_tarea")
        fecha = task_fields.get("fecha_limite_tarea")

        # Manejo seguro de fecha para guardar en Redis (si es str o datetime o null)
        fecha_str = None
        try:
            if isinstance(fecha, datetime):
                fecha_str = fecha.isoformat()
            elif isinstance(fecha, str):
                fecha_str = datetime.fromisoformat(fecha).isoformat()
        except Exception as e:
            print(f"[ERROR al parsear fecha]: {e}")
            fecha_str = None

        # Paso 4: Si falta algo, guardar draft y preguntar
        if not nombre or fecha_str is None:
            print("[ERROR]: Falta información para crear la tarea")
            partial_data = {
                "nombre_tarea": nombre,
                "descripcion_tarea": descripcion,
                "fecha_limite_tarea": fecha_str
            }
            await redis.set(f"draft:schedule_task:{user_id_str}", json.dumps(partial_data), ex=3600)

            missing = []
            if not nombre:
                missing.append("el nombre de la tarea")
            if not fecha_str:
                missing.append("la fecha límite")
            missing_msg = " y ".join(missing)
            mensaje_missing = f"Necesito {missing_msg} para agendar la tarea. ¿Podés indicármelo?"

            response_incompleto: str = await stylize_response(context, "crear_tarea", mensaje_missing)
            return "tarea_incompleta", mensaje_missing, "incomplete"

        # Paso 5: Crear el objeto Pydantic
        try:
            fecha_dt = (
                datetime.fromisoformat(fecha_str)
                if isinstance(fecha_str, str) and fecha_str
                else None
            )
            if not fecha_dt:
                print("[ERROR]: Fecha inválida", fecha_str)
                raise ValueError("Fecha inválida")

            task_data = TaskCreate(
                nombre_tarea=nombre,
                descripcion_tarea=descripcion,
                fecha_limite_tarea=fecha_dt
            )
        except Exception as e:
            print(f"[ERROR al construir TaskCreate]: {e}")
            return "error", "Los datos no son válidos para crear la tarea. Intentalo de nuevo.", "error"

        # Paso 6: Crear la tarea en base de datos
        await redis.delete(f"draft:schedule_task:{user_id_str}")
        created_task = create_task_service(
            db=db,
            task_in=task_data,
            user_id=user_id
        )
        context = await context_service.get_context(user_id_str)

        if created_task is None:
            return "error", "No se pudo crear la tarea. Intentalo de nuevo.", "error"

        # Paso 7: Limpiar el contexto de conversación
        await context_service.clear_context(user_id_str)

        confirmation_msg = (
            f"Tarea creada: '{created_task.nombre_tarea}' "
            f"para el {created_task.fecha_limite_tarea.strftime('%d/%m/%Y %H:%M')}."
        )

        response_create: str = await stylize_response(context, "crear_tarea", confirmation_msg)
        return "tarea_creada", response_create, "success"

    if intent == "update_task":
        return "¿Podés decirme cuál es la tarea a actualizar y qué cambio querés hacer?"

    if intent == "delete_task":
        return "¿Cuál es la tarea que querés eliminar? Necesito su nombre o ID."

    return "No reconocí la intención. Probá con otra forma de decirlo."

def get_intent_prompt(user_input: str):
    return f"""
        Actuá como un clasificador de intenciones para un agente conversacional que agenda y consulta tareas.
            
        Intenciones disponibles:

            - greet → Saludo
            - goodbye → Despedida
            - schedule_task → Crear nueva tarea
            - consult_tasks → Consultar tareas
            - delete_task → Eliminar tarea
            - update_task → Modificar tarea
            - next_task → Próxima tarea
            - missing_info → Falta información para ejecutar
            - clarification → El usuario no entendió
            - fallback → Mensaje irrelevante
            - smalltalk → Comentarios triviales

        Dado este mensaje:

        “{user_input}”

        Respondé solo con el identificador de la intención (por ejemplo: schedule_task).
        """.strip()

def parse_date_range_response(raw_json: str) -> tuple[Optional[datetime], Optional[datetime]]:
    try:
        cleaned = raw_json.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned)

        start = (
            datetime.combine(date.fromisoformat(data["fecha_inicio"]), time.min)
            if data["fecha_inicio"] else None
        )
        end = (
            datetime.combine(date.fromisoformat(data["fecha_fin"]), time.max)
            if data["fecha_fin"] else None
        )

        return start, end

    except Exception as e:
        print(f"[ERROR parse_date_range_response]: {e}")
        return None, None

def parse_task_fields_from_llm(raw_json: str) -> Optional[dict]:
    try:
        cleaned = raw_json.strip().replace("```json", "").replace("```", "").strip()
        if not cleaned.startswith("{"):
            print(f"[ERROR]: El modelo no devolvió un JSON válido: {cleaned}")
            return None

        data = json.loads(cleaned)

        if isinstance(data.get("fecha_limite_tarea"), str):
            data["fecha_limite_tarea"] = datetime.fromisoformat(data["fecha_limite_tarea"])

        return data
    except Exception as e:
        print(f"[ERROR al convertir respuesta del LLM a TaskCreate]: {e}")
        return None

def build_date_range_prompt(context: list, user_input: str) -> str:
    actual_date = datetime.now().isoformat()
    context_lines = "\n".join(f"{m['role']}: {m['content']}" for m in context[-6:])
    prompt = f"""
        Sos un asistente que ayuda a consultar tareas. Tu tarea es detectar si el usuario se refiere a un rango de tiempo y devolverlo en formato JSON.

        ### Instrucciones:
        - Usa la fecha de hoy: {actual_date}, para tener contexto
        - Analizá la entrada y contexto para determinar el rango de fechas que desea consultar.
        - Si dice "hoy", "mañana", "el viernes", etc., devolvé la fecha exacta.
        - Si no se especifica rango, devolvé `null` en ambos campos.
        - El formato debe ser:

        {{
          "fecha_inicio": "YYYY-MM-DD" | null,
          "fecha_fin": "YYYY-MM-DD" | null
        }}

        ### Contexto:
        {context_lines}

        ### Entrada del usuario:
        {user_input}

        ### Tu respuesta (solo JSON):
        """.strip()
    response = llm.invoke(prompt)
    return str(response.content).strip()

def build_fused_schedule_prompt(context: list, user_input: str, draft_json: Optional[str]) -> str:
    context_lines = "\n".join(f"{m['role']}: {m['content']}" for m in context)

    draft = {}
    if draft_json:
        try:
            draft = json.loads(draft_json)
        except Exception as e:
            print(f"[ERROR al parsear draft]: {e}")
            draft = {}

    nombre = draft.get("nombre_tarea", None)
    fecha = draft.get("fecha_limite_tarea", None)
    descripcion = draft.get("descripcion_tarea", None)
    now_iso = datetime.now().isoformat()

    prompt = f"""
    Sos un asistente basico que ayuda a crear tareas.

    La fecha y hora actual es: {now_iso}

    Tu objetivo es extraer solo los campos requeridos para crear una tarea. no ofrezcan muchas ejemplos, solo uno sencillo, tampoco ofrezca adicionar información adicional al que se te indican las propiedades El usuario puede dar información en varios pasos, y vos debés combinar lo anterior con lo actual.

    Respondé únicamente con un JSON válido con la siguiente estructura:

    {{
      "nombre_tarea": string,               // obligatorio
      "descripcion_tarea": string | null,  // opcional
      "fecha_limite_tarea": string | null  // obligatorio, formato ISO 8601, ej: "2025-07-23T10:00:00"
    }}

    ### Historial de conversación:
    {context_lines}

    ### Borrador anterior de la tarea:
    {{
      "nombre_tarea": {json.dumps(nombre)},
      "descripcion_tarea": {json.dumps(descripcion)},
      "fecha_limite_tarea": {json.dumps(fecha)}
    }}

    ### Entrada actual del usuario:
    "{user_input}"

    IMPORTANTE:
    - Si el usuario dice “mañana”, “el viernes”, “esta noche”, etc., convertilo a una fecha y hora exacta (formato ISO 8601).
    - Si el usuario no proporciona una hora, pon por defecto las 10:00:00
    - Si algún campo no está claro, ponelo como `null`.
    - Respondé exclusivamente con JSON válido. No uses explicaciones, texto extra, markdown, emojis ni formato conversacional.
    - No uses como nombre de tarea frases como "crear una tarea" o "nueva tarea". El nombre debe ser una acción concreta como "enviar informe a finanzas".
    - El resultado debe comenzar con '{{' y ser 100% válido para `json.loads()`.

    Solo devolvé el JSON.
    """.strip()
    response = llm.invoke(prompt)
    return str(response.content).strip()

async def stylize_response(context: List[dict], intent: str, base_response: str) -> str:
    context_text = "\n".join(f"{m['role']}: {m['content']}" for m in context[-6:])  # últimos 6
    prompt = f"""
        Verificá el 'Contexto de conversación' y basa tu respuesta para ofrecer al usuario el siguiente paso en función al 'mensaje base del sistema' dentro del intento '{intent}'.
        tu respuesta debe ser natural, directa y modificar el 'mensaje base del sistema', pero no cambiar su proposito a menos que sea un intento de 'charlar', entonces trata de responder de forma corta pero efectiva.

        ### Contexto de conversación:
        {context_text}

        ### Mensaje base del sistema:
        {base_response}

        ### Tu respuesta final:
        """.strip()

    response = llm.invoke(prompt)
    return str(response.content).strip()
