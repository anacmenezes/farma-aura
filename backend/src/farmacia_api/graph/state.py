
from typing import Any, TypedDict


class FarmaAuraState(TypedDict, total=False):
    user_request: str
    cep: str | None
    search_results: dict[str, Any]
    final_response: str
    error: str | None
