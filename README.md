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
