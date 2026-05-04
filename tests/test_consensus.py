import pytest
from app.graph.consensus import all_agents_approve, review_blocks, should_continue


def _make_review(
    verdict="approve",
    confidence=0.95,
    correct=True,
    secure=True,
    working=True,
    issues=None,
    provider="openai",
):
    return {
        "agent_name": "Test Agent",
        "provider": provider,
        "verdict": verdict,
        "confidence": confidence,
        "correct": correct,
        "secure": secure,
        "working": working,
        "summary": "Test summary",
        "issues": issues or [],
        "rebuttal": {"accepted_points": [], "rejected_points": [], "changed_mind": False},
    }


def _make_issue(severity="low", blocks_approval=False):
    return {
        "id": "issue-1",
        "type": "bug",
        "severity": severity,
        "file": None,
        "line": None,
        "description": "A test issue",
        "recommendation": "Fix it",
        "blocks_approval": blocks_approval,
    }


# --- review_blocks ---


def test_blocks_when_verdict_not_approve():
    assert review_blocks(_make_review(verdict="needs_changes"))
    assert review_blocks(_make_review(verdict="reject"))


def test_blocks_when_correct_false():
    assert review_blocks(_make_review(correct=False))


def test_blocks_when_secure_false():
    assert review_blocks(_make_review(secure=False))


def test_blocks_when_working_false():
    assert review_blocks(_make_review(working=False))


def test_blocks_when_confidence_below_threshold():
    assert review_blocks(_make_review(confidence=0.79))


def test_does_not_block_at_confidence_threshold():
    assert not review_blocks(_make_review(confidence=0.80))


def test_blocks_on_critical_issue():
    assert review_blocks(_make_review(issues=[_make_issue(severity="critical")]))


def test_blocks_on_high_security_issue():
    assert review_blocks(_make_review(issues=[_make_issue(severity="high")]))


def test_does_not_block_on_medium_issue():
    assert not review_blocks(_make_review(issues=[_make_issue(severity="medium")]))


def test_blocks_when_issue_has_blocks_approval_flag():
    assert review_blocks(
        _make_review(issues=[_make_issue(severity="low", blocks_approval=True)])
    )


def test_approve_passes_with_clean_review():
    assert not review_blocks(_make_review())


# --- all_agents_approve ---


def test_all_agents_approve_requires_three_reviews():
    reviews = [_make_review(provider="openai"), _make_review(provider="anthropic")]
    assert not all_agents_approve(reviews)


def test_all_agents_approve_with_three_clean_reviews():
    reviews = [
        _make_review(provider="openai"),
        _make_review(provider="anthropic"),
        _make_review(provider="gemini"),
    ]
    assert all_agents_approve(reviews)


def test_all_agents_approve_fails_if_one_blocks():
    reviews = [
        _make_review(provider="openai"),
        _make_review(provider="anthropic", verdict="needs_changes"),
        _make_review(provider="gemini"),
    ]
    assert not all_agents_approve(reviews)


# --- should_continue ---


def test_should_continue_returns_finalize_on_consensus():
    state = {
        "reviews": [
            _make_review(provider="openai"),
            _make_review(provider="anthropic"),
            _make_review(provider="gemini"),
        ],
        "round_number": 0,
    }
    assert should_continue(state) == "finalize"


def test_should_continue_returns_debate_when_no_consensus():
    state = {
        "reviews": [
            _make_review(provider="openai", verdict="needs_changes"),
            _make_review(provider="anthropic"),
            _make_review(provider="gemini"),
        ],
        "round_number": 0,
    }
    assert should_continue(state) == "debate"


def test_should_continue_returns_finalize_at_max_rounds(monkeypatch):
    import app.graph.consensus as consensus_mod
    monkeypatch.setattr(consensus_mod, "MAX_ROUNDS", 3)
    state = {
        "reviews": [
            _make_review(provider="openai", verdict="needs_changes"),
            _make_review(provider="anthropic"),
            _make_review(provider="gemini"),
        ],
        "round_number": 3,
    }
    assert should_continue(state) == "finalize"
