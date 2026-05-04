import os

MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE_TO_APPROVE", "0.80"))
MAX_ROUNDS = int(os.getenv("MAX_DEBATE_ROUNDS", "3"))


def review_blocks(review: dict) -> bool:
    if review["verdict"] != "approve":
        return True
    if not (review["correct"] and review["secure"] and review["working"]):
        return True
    if review["confidence"] < MIN_CONFIDENCE:
        return True
    for issue in review["issues"]:
        if issue["blocks_approval"]:
            return True
        if issue["severity"] in {"high", "critical"}:
            return True
    return False


def all_agents_approve(reviews: list[dict]) -> bool:
    if len(reviews) != 3:
        return False
    return not any(review_blocks(r) for r in reviews)


def should_continue(state: dict) -> str:
    if all_agents_approve(state["reviews"]):
        return "finalize"
    if state["round_number"] >= MAX_ROUNDS:
        return "finalize"
    return "debate"
