from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import AIService
from app.services.risk_classifier_hybrid import HybridRiskClassifier

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    emotion: str
    emotion_confidence: float
    distortion: str
    distortion_confidence: float
    socratic_question: str
    risk_score: float
    flag_riesgo_suicida: bool
    risk_reason: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_thought(request: AnalyzeRequest):
    if not request.text or len(request.text.strip()) < 3:
        raise HTTPException(
            status_code=400, detail="El texto debe tener al menos 3 caracteres"
        )

    result = await AIService.analyze_thought(request.text)
    risk_classifier = HybridRiskClassifier()
    risk_score, flag, reason = risk_classifier.calculate_risk_score(request.text)

    return {
        "emotion": result["emotion"],
        "emotion_confidence": result["emotion_confidence"],
        "distortion": result["distortion"],
        "distortion_confidence": result["distortion_confidence"],
        "socratic_question": result["socratic_question"],
        "risk_score": risk_score,
        "flag_riesgo_suicida": flag,
        "risk_reason": reason,
    }