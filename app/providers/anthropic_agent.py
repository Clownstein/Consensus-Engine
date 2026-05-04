import os

import anthropic

from app.prompts import SECURITY_PROMPT, build_agent_user_prompt
from app.schemas import REVIEW_SCHEMA, validate_review

_client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

# Global capture instance (will be set by batch reviewer)
_capture = None


def set_api_capture(capture_instance):
    """Set the API capture instance to use."""
    global _capture
    _capture = capture_instance


def _extract_tool_input(message) -> dict:
    for block in message.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "submit_review":
            return block.input
    raise ValueError("Claude did not return submit_review tool input")


async def run_anthropic_security(
    review_context: dict,
    previous_reviews: list[dict],
    round_number: int,
) -> dict:
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    user_content = build_agent_user_prompt(review_context, previous_reviews, round_number)
    
    # Capture the request
    if _capture:
        request_id = _capture.capture_request(
            provider="anthropic",
            model=model,
            system_prompt=SECURITY_PROMPT,
            user_message=user_content,
            metadata={"round": round_number, "pr": review_context.get("pr_number")}
        )

    message = await _client.messages.create(
        model=model,
        max_tokens=4096,
        system=SECURITY_PROMPT,
        tools=[
            {
                "name": "submit_review",
                "description": "Submit the structured code review verdict.",
                "input_schema": REVIEW_SCHEMA,
            }
        ],
        tool_choice={"type": "tool", "name": "submit_review"},
        messages=[
            {
                "role": "user",
                "content": user_content,
            }
        ],
    )
    
    # Capture the response (extract tool input as response text)
    if _capture:
        tool_input = _extract_tool_input(message)
        _capture.capture_response(
            request_id=request_id,
            response=str(tool_input),  # Tool input becomes the response
            finish_reason=message.stop_reason,
            usage={"input_tokens": message.usage.input_tokens, "output_tokens": message.usage.output_tokens}
        )

    return validate_review(_extract_tool_input(message))
