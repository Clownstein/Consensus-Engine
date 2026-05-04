from typing import Any, TypedDict


class ReviewState(TypedDict):
    review_context: dict[str, Any]
    round_number: int
    reviews: list[dict[str, Any]]
    history: list[dict[str, Any]]
    approved: bool
    done: bool
    final_summary: str
