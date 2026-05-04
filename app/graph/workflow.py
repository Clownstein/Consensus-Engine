import asyncio

from langgraph.graph import END, StateGraph

from app.graph.consensus import all_agents_approve, should_continue
from app.graph.state import ReviewState
from app.providers.anthropic_agent import run_anthropic_security
from app.providers.gemini_agent import run_gemini_runtime
from app.providers.openai_agent import run_openai_architect


async def initial_review(state: ReviewState) -> ReviewState:
    ctx = state["review_context"]
    round_number = 0
    reviews = await asyncio.gather(
        run_openai_architect(ctx, [], round_number),
        run_anthropic_security(ctx, [], round_number),
        run_gemini_runtime(ctx, [], round_number),
    )
    reviews = list(reviews)
    return {
        **state,
        "round_number": round_number,
        "reviews": reviews,
        "history": [{"round": round_number, "reviews": reviews}],
    }


async def debate_round(state: ReviewState) -> ReviewState:
    ctx = state["review_context"]
    round_number = state["round_number"] + 1
    previous = state["reviews"]
    reviews = await asyncio.gather(
        run_openai_architect(ctx, previous, round_number),
        run_anthropic_security(ctx, previous, round_number),
        run_gemini_runtime(ctx, previous, round_number),
    )
    reviews = list(reviews)
    history = state["history"] + [{"round": round_number, "reviews": reviews}]
    return {**state, "round_number": round_number, "reviews": reviews, "history": history}


def finalize(state: ReviewState) -> ReviewState:
    approved = all_agents_approve(state["reviews"])
    return {
        **state,
        "approved": approved,
        "done": True,
        "final_summary": (
            "Approved by all agents."
            if approved
            else "Changes requested by one or more agents."
        ),
    }


def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("initial_review", initial_review)
    graph.add_node("debate", debate_round)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("initial_review")
    graph.add_conditional_edges(
        "initial_review",
        should_continue,
        {"debate": "debate", "finalize": "finalize"},
    )
    graph.add_conditional_edges(
        "debate",
        should_continue,
        {"debate": "debate", "finalize": "finalize"},
    )
    graph.add_edge("finalize", END)
    return graph.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_review_graph(review_context: dict) -> dict:
    initial_state: ReviewState = {
        "review_context": review_context,
        "round_number": 0,
        "reviews": [],
        "history": [],
        "approved": False,
        "done": False,
        "final_summary": "",
    }
    return await _get_graph().ainvoke(initial_state)
