from jsonschema import validate, ValidationError

REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "agent_name",
        "provider",
        "verdict",
        "confidence",
        "correct",
        "secure",
        "working",
        "summary",
        "issues",
        "rebuttal",
    ],
    "properties": {
        "agent_name": {"type": "string"},
        "provider": {"type": "string", "enum": ["openai", "anthropic", "gemini"]},
        "verdict": {"type": "string", "enum": ["approve", "needs_changes", "reject"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "correct": {"type": "boolean"},
        "secure": {"type": "boolean"},
        "working": {"type": "boolean"},
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "id",
                    "type",
                    "severity",
                    "file",
                    "line",
                    "description",
                    "recommendation",
                    "blocks_approval",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "bug",
                            "security",
                            "test",
                            "performance",
                            "maintainability",
                            "style",
                            "docs",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "file": {"type": ["string", "null"]},
                    "line": {"type": ["integer", "null"]},
                    "description": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "blocks_approval": {"type": "boolean"},
                },
            },
        },
        "rebuttal": {
            "type": "object",
            "additionalProperties": False,
            "required": ["accepted_points", "rejected_points", "changed_mind"],
            "properties": {
                "accepted_points": {"type": "array", "items": {"type": "string"}},
                "rejected_points": {"type": "array", "items": {"type": "string"}},
                "changed_mind": {"type": "boolean"},
            },
        },
    },
}


def validate_review(data: dict) -> dict:
    try:
        validate(instance=data, schema=REVIEW_SCHEMA)
    except ValidationError as exc:
        raise ValueError(f"Invalid agent review JSON: {exc.message}") from exc
    return data
