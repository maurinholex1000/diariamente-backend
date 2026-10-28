from app.routes.auth import router as auth_router
from app.routes.diary import router as diary_router
from app.routes.ai import router as ai_router
from app.routes.consent import router as consent_router
from app.routes.therapist import router as therapist_router
from app.routes.notifications import router as notifications_router
from app.routes.legal import router as legal_router

__all__ = [
    "auth_router", "diary_router", "ai_router",
    "consent_router", "therapist_router",
    "notifications_router", "legal_router",
]