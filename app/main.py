from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routes import auth, diary, ai, consent, therapist, notifications, legal

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {"message": f"Bienvenido a {settings.app_name}", "status": "operativo"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}