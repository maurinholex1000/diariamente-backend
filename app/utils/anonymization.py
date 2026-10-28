import hashlib
from typing import Dict


class AnonymizationService:
    @staticmethod
    def anonymize_patient(patient_data: Dict) -> Dict:
        patient_id = patient_data.get("id", 0)
        return {
            "patient_hash": hashlib.sha256(
                f"patient_{patient_id}".encode()
            ).hexdigest()[:12],
            "age_range": "adulto",
        }

    @staticmethod
    def anonymize_for_research(entry: Dict) -> Dict:
        return {
            "emotion": entry.get("detected_emotion"),
            "distortion": entry.get("detected_distortion"),
            "risk_score": entry.get("risk_score"),
            "created_at": entry.get("created_at"),
        }


anonymization_service = AnonymizationService()