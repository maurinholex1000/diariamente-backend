from typing import Optional, Dict, Any
import hashlib


class AICacheService:
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Any] = {}
        self._max_size = max_size

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.strip().lower().encode()).hexdigest()

    def get(self, text: str) -> Optional[Dict]:
        return self._cache.get(self._hash(text))

    def set(self, text: str, result: Dict):
        if len(self._cache) >= self._max_size:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[self._hash(text)] = result

    def clear(self):
        self._cache.clear()


ai_cache = AICacheService()