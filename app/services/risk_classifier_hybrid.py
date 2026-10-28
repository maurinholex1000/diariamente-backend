from pysentimiento import create_analyzer
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class HybridRiskClassifier:
    def __init__(self):
        print("🔄 Cargando modelos para RiskClassifier Híbrido...")
        self.emotion_analyzer = create_analyzer(task="emotion", lang="es")
        self.sentiment_analyzer = create_analyzer(task="sentiment", lang="es")
        print("✅ Modelos de IA cargados")

        self.crisis_keywords = {
            "muerte": 2.0, "morir": 2.0, "matarme": 2.5,
            "suicid": 2.5, "terminar con todo": 2.5,
            "no quiero vivir": 2.5, "quiero morirme": 2.5,
            "desaparecer": 2.0, "acabar con mi vida": 2.5,
            "no despertar": 2.0, "dejar de existir": 2.0,
            "me quiero morir": 2.5,
        }
        self.hopelessness_keywords = {
            "nunca": 0.8, "siempre igual": 0.8,
            "no hay solución": 1.2, "no tiene sentido": 1.2,
            "para qué": 0.8, "no puedo cambiar": 1.0,
            "es inútil": 1.0, "no va a mejorar": 1.0,
            "nada cambia": 0.8, "no vale la pena": 1.2,
        }
        self.worthlessness_keywords = {
            "inútil": 1.2, "fracasado": 1.2,
            "no sirvo": 1.2, "no valgo": 1.2,
            "soy un estorbo": 1.5, "soy una carga": 1.5,
            "todos estarían mejor sin mí": 2.0,
        }
        self.high_risk_emotions = ["sadness", "anger", "fear", "disgust"]
        self.IA_RISK_THRESHOLD = 0.60
        self.CRISIS_THRESHOLD = 0.85

    def calculate_risk_score(self, text: str) -> Tuple[float, bool, str]:
        text_lower = text.lower()
        reasons = []
        crisis_detected = False

        # IA
        ia_score = 0.0
        try:
            emotion_result = self.emotion_analyzer.predict(text)
            top_emotion = max(emotion_result.probas, key=emotion_result.probas.get)
            top_conf = emotion_result.probas[top_emotion]

            sentiment_result = self.sentiment_analyzer.predict(text)
            neg_prob = sentiment_result.probas.get("NEG", 0.0)

            if top_emotion in self.high_risk_emotions:
                ia_score += 0.35 * top_conf
                reasons.append(f"IA: {top_emotion} ({top_conf:.0%})")

            if neg_prob > 0.7:
                ia_score += 0.25 * neg_prob
                reasons.append(f"IA: negativo ({neg_prob:.0%})")

            ia_score = min(ia_score, 0.6)
        except Exception as e:
            logger.error(f"Error IA: {e}")

        # Reglas
        rule_score = 0.0
        hopelessness_count = 0

        for kw, w in self.crisis_keywords.items():
            if kw in text_lower:
                rule_score += w
                if w >= 2.0:
                    crisis_detected = True

        for kw, w in self.hopelessness_keywords.items():
            if kw in text_lower:
                rule_score += w
                hopelessness_count += 1

        for kw, w in self.worthlessness_keywords.items():
            if kw in text_lower:
                rule_score += w

        rule_score = min(rule_score / 10.0, 0.4)
        if crisis_detected or hopelessness_count >= 3:
            rule_score = max(rule_score, 0.35)

        final_score = min(ia_score + rule_score, 1.0)

        ia_risk = ia_score >= self.IA_RISK_THRESHOLD
        score_alto = final_score >= self.CRISIS_THRESHOLD
        flag = ia_risk or score_alto or crisis_detected

        reason = f"Score: {final_score:.2f} (IA: {ia_score:.2f} + Reglas: {rule_score:.2f})"
        if flag:
            reason += " 🚨 ALERTA"

        return final_score, flag, reason

    def get_risk_details(self, text: str) -> Dict:
        text_lower = text.lower()
        emotion_result = self.emotion_analyzer.predict(text)
        top_emotion = max(emotion_result.probas, key=emotion_result.probas.get)
        sentiment_result = self.sentiment_analyzer.predict(text)

        crisis_words = [kw for kw in self.crisis_keywords if kw in text_lower]
        hopeless_words = [kw for kw in self.hopelessness_keywords if kw in text_lower]
        worthless_words = [kw for kw in self.worthlessness_keywords if kw in text_lower]

        score, flag, reason = self.calculate_risk_score(text)

        return {
            "text": text,
            "risk_score": score,
            "flag_riesgo_suicida": flag,
            "reason": reason,
            "ia_analysis": {
                "top_emotion": top_emotion,
                "emotion_confidence": emotion_result.probas[top_emotion],
                "sentiment": sentiment_result.output,
            },
            "keywords_detected": {
                "crisis": crisis_words,
                "hopelessness": hopeless_words,
                "worthlessness": worthless_words,
            },
        }