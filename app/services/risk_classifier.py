from typing import Tuple


class RiskClassifier:
    def __init__(self):
        self.crisis_keywords = {
            "muerte": 2.0, "morir": 2.0, "matarme": 2.5,
            "suicid": 2.5, "terminar con todo": 2.5,
            "no quiero vivir": 2.5, "quiero morirme": 2.5,
            "desaparecer": 2.0, "acabar con mi vida": 2.5,
            "no despertar": 2.0, "dejar de existir": 2.0,
            "no vale la pena": 1.5, "no sirvo para nada": 1.5,
            "todos estarían mejor sin mí": 2.0,
            "soy una carga": 1.5, "no hay salida": 1.5,
            "no puedo más": 1.5, "no aguanto más": 1.5,
            "me quiero morir": 2.5,
        }
        self.hopelessness_keywords = {
            "nunca": 0.8, "siempre igual": 0.8,
            "no hay solución": 1.2, "no tiene sentido": 1.2,
            "para qué": 0.8, "no puedo cambiar": 1.0,
            "es inútil": 1.0, "no va a mejorar": 1.0,
            "nada cambia": 0.8,
        }
        self.worthlessness_keywords = {
            "inútil": 1.2, "fracasado": 1.2,
            "no sirvo": 1.2, "no valgo": 1.2,
            "soy un estorbo": 1.5, "soy una carga": 1.5,
        }

    def calculate_risk_score(self, text: str) -> Tuple[float, bool, str]:
        text_lower = text.lower()
        score = 0.0
        reasons = []
        crisis_detected = False

        for keyword, weight in self.crisis_keywords.items():
            if keyword in text_lower:
                score += weight
                reasons.append(f"Crisis: '{keyword}'")
                if weight >= 2.0:
                    crisis_detected = True

        hopelessness_count = 0
        for keyword, weight in self.hopelessness_keywords.items():
            if keyword in text_lower:
                score += weight
                hopelessness_count += 1

        for keyword, weight in self.worthlessness_keywords.items():
            if keyword in text_lower:
                score += weight

        normalized = min(score / 10.0, 1.0)
        flag = normalized >= 0.85 or crisis_detected or hopelessness_count >= 3
        reason = f"Score: {normalized:.2f}"
        if flag:
            reason += " - ALERTA"

        return normalized, flag, reason