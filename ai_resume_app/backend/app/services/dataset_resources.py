import json
from functools import lru_cache
from pathlib import Path


_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


@lru_cache(maxsize=None)
def load_terms(resource_name: str) -> tuple[str, ...]:
    path = _PROCESSED_DIR / f"{resource_name}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        terms = payload.get("terms", [])
        return tuple(
            term["term"].strip()
            for term in terms
            if isinstance(term, dict) and isinstance(term.get("term"), str)
        )
    except (OSError, json.JSONDecodeError, TypeError):
        return ()