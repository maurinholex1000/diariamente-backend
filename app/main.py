
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routes import (
    auth,
    diary,
    ai,
    consent,
    therapist,
    notifications,
    legal,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # En desarrollo local permitimos crear las tablas automáticamente.
    # En producción utilizaremos migraciones con Alembic.
    if settings.debug:
        Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Orígenes permitidos para desarrollo web local.
# La aplicación React Native nativa no depende de CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(diary.router)
app.include_router(ai.router)
app.include_router(consent.router)
app.include_router(therapist.router)
app.include_router(notifications.router)
app.include_router(legal.router)


@app.get("/")
async def root():
    return {
        "message": f"Bienvenido a {settings.app_name}",
        "status": "operativo",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
    }
