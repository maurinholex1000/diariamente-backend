from pysentimiento import create_analyzer
from typing import Dict, List


class CognitiveAnalyzer:
    def __init__(self):
        print("🔄 Cargando modelo RoBERTuito...")
        self.emotion_analyzer = create_analyzer(task="emotion", lang="es")
        print("✅ Modelo cargado")

        self.emotion_mapping = {
            "joy": "Alegría", "sadness": "Tristeza", "anger": "Enojo",
            "fear": "Miedo", "surprise": "Sorpresa",
            "disgust": "Disgusto", "neutral": "Neutral",
        }

        self.distortion_patterns = {
            "catastrofizacion": {
                "keywords": ["voy a morir", "lo peor", "catástrofe", "desastre", "fatal"],
                "weight": 2,
            },
            "polarizacion": {
                "keywords": ["siempre", "nunca", "todo", "nada", "perfecto", "horrible"],
                "weight": 1.5,
            },
            "sobregeneralizacion": {
                "keywords": ["siempre me pasa", "todos son", "nadie me", "otra vez"],
                "weight": 1.5,
            },
            "etiquetacion": {
                "keywords": ["soy un", "idiota", "inútil", "fracasado", "torpe"],
                "weight": 1.3,
            },
        }

        self.socratic_questions = {
            "catastrofizacion": "¿Qué evidencia real tenés de que va a pasar lo peor?",
            "polarizacion": "¿Hay algún punto medio entre estas dos opciones?",
            "sobregeneralizacion": "¿Un evento aislado realmente define todo?",
            "etiquetacion": "¿Podés describir la conducta específica en lugar de etiquetarte?",
        }

    def detect_distortions(self, text: str) -> List[Dict]:
        text_lower = text.lower()
        detected = []
        for distortion, config in self.distortion_patterns.items():
            score = sum(
                config["weight"] for kw in config["keywords"] if kw in text_lower
            )
            if score > 0:
                detected.append({
                    "type": distortion,
                    "confidence": min(score / 5, 0.95),
                })
        if not detected:
            detected.append({"type": "sin_distorsion", "confidence": 0.8})
        return detected

    def analyze(self, text: str) -> Dict:
        emotion_result = self.emotion_analyzer.predict(text)
        top = max(emotion_result.probas, key=emotion_result.probas.get)
        emotion = self.emotion_mapping.get(top, "Neutral")
        emotion_confidence = emotion_result.probas[top]

        distortions = self.detect_distortions(text)
        primary = max(distortions, key=lambda x: x["confidence"])

        return {
            "emotion": emotion,
            "emotion_confidence": round(emotion_confidence * 100, 2),
            "distortion": primary["type"],
            "distortion_confidence": round(primary["confidence"] * 100, 2),
            "socratic_question": self.socratic_questions.get(
                primary["type"],
                "¿Qué pensamiento alternativo más realista podrías tener?",
            ),
        }