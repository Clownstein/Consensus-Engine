import pytest

from app.providers.gemini_agent import _extract_first_json_object


def test_extract_first_json_object_parses_plain_json():
    parsed = _extract_first_json_object('{"ok": true, "count": 1}')
    assert parsed == {"ok": True, "count": 1}


def test_extract_first_json_object_handles_braces_inside_string():
    response = (
        "prefix text\n"
        '{"summary":"Use {token} safely","issues":[],"rebuttal":{"accepted_points":[],"rejected_points":[],"changed_mind":false}}\n'
        "suffix text"
    )
    parsed = _extract_first_json_object(response)
    assert parsed["summary"] == "Use {token} safely"
    assert parsed["issues"] == []


def test_extract_first_json_object_raises_when_missing_json():
    with pytest.raises(ValueError, match="Could not parse JSON from Gemini response"):
        _extract_first_json_object("no json here")
