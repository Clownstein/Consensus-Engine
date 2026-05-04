import pytest
from app.schemas import validate_review


def _valid_review(**overrides):
    base = {
        "agent_name": "Test Agent",
        "provider": "openai",
        "verdict": "approve",
        "confidence": 0.9,
        "correct": True,
        "secure": True,
        "working": True,
        "summary": "Looks good.",
        "issues": [],
        "rebuttal": {
            "accepted_points": [],
            "rejected_points": [],
            "changed_mind": False,
        },
    }
    base.update(overrides)
    return base


def test_valid_review_passes():
    result = validate_review(_valid_review())
    assert result["verdict"] == "approve"


def test_missing_required_field_raises():
    data = _valid_review()
    del data["verdict"]
    with pytest.raises(ValueError, match="Invalid agent review JSON"):
        validate_review(data)


def test_invalid_provider_enum_raises():
    with pytest.raises(ValueError):
        validate_review(_valid_review(provider="cohere"))


def test_invalid_verdict_enum_raises():
    with pytest.raises(ValueError):
        validate_review(_valid_review(verdict="lgtm"))


def test_confidence_below_range_raises():
    with pytest.raises(ValueError):
        validate_review(_valid_review(confidence=-0.1))


def test_confidence_above_range_raises():
    with pytest.raises(ValueError):
        validate_review(_valid_review(confidence=1.1))


def test_extra_top_level_field_raises():
    data = _valid_review()
    data["unexpected_field"] = "oops"
    with pytest.raises(ValueError):
        validate_review(data)


def test_valid_issue_passes():
    issue = {
        "id": "issue-1",
        "type": "security",
        "severity": "high",
        "file": "app/main.py",
        "line": 42,
        "description": "SQL injection risk",
        "recommendation": "Use parameterized queries",
        "blocks_approval": True,
    }
    result = validate_review(_valid_review(issues=[issue]))
    assert result["issues"][0]["severity"] == "high"


def test_issue_with_null_file_and_line_passes():
    issue = {
        "id": "issue-2",
        "type": "docs",
        "severity": "low",
        "file": None,
        "line": None,
        "description": "Missing docstring",
        "recommendation": "Add docstring",
        "blocks_approval": False,
    }
    result = validate_review(_valid_review(issues=[issue]))
    assert result["issues"][0]["file"] is None


def test_invalid_issue_severity_raises():
    issue = {
        "id": "issue-3",
        "type": "bug",
        "severity": "extreme",  # not in enum
        "file": None,
        "line": None,
        "description": "Bad",
        "recommendation": "Fix",
        "blocks_approval": False,
    }
    with pytest.raises(ValueError):
        validate_review(_valid_review(issues=[issue]))


def test_invalid_issue_type_raises():
    issue = {
        "id": "issue-4",
        "type": "unknown_type",
        "severity": "low",
        "file": None,
        "line": None,
        "description": "Bad",
        "recommendation": "Fix",
        "blocks_approval": False,
    }
    with pytest.raises(ValueError):
        validate_review(_valid_review(issues=[issue]))


def test_needs_changes_verdict_passes():
    result = validate_review(_valid_review(verdict="needs_changes"))
    assert result["verdict"] == "needs_changes"


def test_reject_verdict_passes():
    result = validate_review(_valid_review(verdict="reject"))
    assert result["verdict"] == "reject"


def test_anthropic_provider_passes():
    result = validate_review(_valid_review(provider="anthropic"))
    assert result["provider"] == "anthropic"


def test_gemini_provider_passes():
    result = validate_review(_valid_review(provider="gemini"))
    assert result["provider"] == "gemini"


def test_rebuttal_with_points_passes():
    result = validate_review(
        _valid_review(
            rebuttal={
                "accepted_points": ["Good point about null handling"],
                "rejected_points": ["Unsubstantiated injection claim"],
                "changed_mind": True,
            }
        )
    )
    assert result["rebuttal"]["changed_mind"] is True
