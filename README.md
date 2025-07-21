# Task AI Backend Documentation

documentación del proyecto de backend de generative task ai.
Backend hecho con FastAPI, Docker, Postgres, Redis, y GEMINI AI como LLM a través de langchain

## requerimientos:
- Una API HTTP (REST) que reciba:
  - user_input (string): Mensaje del usuario en lenguaje natural.
    - Se envia dentro del body en JSON como {"user_input": "y para el miercoles?"}
  - session_id (string): Identificador único de la sesión del usuario.
    - Se envia a través del AccessToken como encabezado bearer

## Descripción tecnica
- se decide utilizar redis para el contexto (10 últimos mensajes) por la rápides de este y la facilidad para borrar y escribir nuevos datos
- se decide usar una base de datos Postgres para almacenar la información de tareas, usuario, etc, es sencillo y rápido
- se decide usar FAST API por la rápidez de desarollo een este framwork
- use GEMINI AI por 2.0 FLASH, modelo capaz y barato de usar, suficiente
- se decide usar python por la por la compatibilidad de este lenguaje con las librerias LLM
- se usan 3 prompts para el procesamiento de los datos:
  - uno para adivinar la intención.
  - uno para parsear la respuesta del usuario y construir la data enviar a los servicios y se creen los datos
  - uno para devolver la respuesta al usuario de forma natural y también invitarlo según el contexto a continuar más tareas.

El detalle de los prompt que se usan esta en: `app/services/chat_servicios.py`

## EJEMPLO CHARLA
  - usuario: Hola, como estas
  - asistente: ¡Hola! Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?
  - usuario: quiero agendar una tarea
  - asistente: Necesito el nombre de la tarea y la fecha límite para agendar la tarea. ¿Podés indicármelo?
  - para el miercoles a las 12, ir a la oficina a travbajar
  - Tarea creada: 'ir a la oficina a travbajar' para el 23/07/2025 12:00. ¿Necesitas agendar alguna otra tarea?
  - si, para el jueves, tengo un partido a las 19 horas
  - Tarea creada: 'partido' para el 24/07/2025 19:00. ¿Hay algo más que deba agendar?
  - muestrame las tareas que tengo para el martes
  - Estas son tus tareas para el martes:
      Llevar el auto al mecánico (22/07 02:16), ¿Deseas cambiar la fecha?
      Llevar a los niños al colegio (22/07 10:00), ¿Deseas cambiar la fecha?
      Limpiar los cuartos (22/07 10:00), ¿Deseas cambiar la fecha?
      ¿Hay algo más en lo que te pueda ayudar?
  - no gracias,
  - ¡Perfecto! ¡Hasta luego y que tengas un gran día! Si necesitas algo más, no dudes en volver.

## Table of Contents
1.  [Project Overview](#project-overview)
2.  [Architecture](#architecture)
    *   [Clean Architecture] : dividido en carpetas:
      - domain: logica de negocio, donde se detallan la logica de las bases de datos.
      - services: logica se servicios, funciones que sirven para realizar conexiones externas, porcesar datos, agnostico para otros tipos de modulos.
      - core: logica de dominio, donde se realizan las conexión a las bases de datos e infrastructura interna.
3.  [Design Patterns](#design-patterns)
    *   [CLEAN CODE Pattern] : patron de diseño clean code pero enfocado a un modelo más pragmatico, la idea es poder abstraer las conexiones de la aplicación de modo que sea fácil de escalar, realizar más conexiones, acoplat nuevas conexiones o desacoplar con un minimo de interferencia en el funcionamiento de al app.
4.  [Technologies Used](#technologies-used)
    *   [Redis] : usado para almacenar el contexto de las conversaciones de cada usuario, maximo 10. brinda alta disponibilidad a la hora se servir datos. 
    *   [JWT (JSON Web Tokens)](#jwt-json-web-tokens): usado para la creación del token de acceso en frontend
    *   [Bcrypt](#bcrypt) : usado para encriptar el token de acceso en frontend
6.  [Setup and Installation](#setup-and-installation)
    *   [Prerequisites] :
      - Docker
    *   [Environment Variables] : 
      - `env.example -> .env` para realizar pruebas de forma local
    *   [Installing Dependencies]
      - `pip install -r requirements.txt`
      - O simplemente ejecutar docker.
    *   [Running the Application] : 
      - En el directorio raíz ejecutar: `docker compose up -d --build`
      - Posiblemente el contenedor de base de datos despliegue antes que el de backend, ejectur nuevamente `docker compose up -d`
7.  [API Endpoints]
      - http://localhost:5500/docs#/
