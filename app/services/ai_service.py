from app.ml.cognitive_analyzer import CognitiveAnalyzer
from app.services.ai_cache_service import ai_cache

_analyzer = None


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = CognitiveAnalyzer()
    return _analyzer


class AIService:
    @staticmethod
    async def analyze_thought(text: str) -> dict:
        cached = ai_cache.get(text)
        if cached:
            return cached
        result = get_analyzer().analyze(text)
        ai_cache.set(text, result)
        return result