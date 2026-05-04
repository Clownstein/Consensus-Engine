import json
import os

from openai import AsyncOpenAI

from app.prompts import RUNTIME_PROMPT, build_agent_user_prompt
from app.schemas import validate_review

_client = AsyncOpenAI(
    api_key=os.environ.get("GEMINI_API_KEY", ""),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Global capture instance (will be set by batch reviewer)
_capture = None


def set_api_capture(capture_instance):
    """Set the API capture instance to use."""
    global _capture
    _capture = capture_instance


def _extract_first_json_object(response_text: str) -> dict:
    stripped = response_text.strip()
    decoder = json.JSONDecoder()
    for idx, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stripped[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
    raise ValueError("Could not parse JSON from Gemini response")


async def run_gemini_runtime(
    review_context: dict,
    previous_reviews: list[dict],
    round_number: int,
) -> dict:
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    user_content = build_agent_user_prompt(review_context, previous_reviews, round_number)
    
    # Capture the request
    if _capture:
        request_id = _capture.capture_request(
            provider="google",
            model=model,
            system_prompt=RUNTIME_PROMPT,
            user_message=user_content,
            metadata={"round": round_number, "pr": review_context.get("pr_number")}
        )

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RUNTIME_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )

    response_text = response.choices[0].message.content
    
    # Capture the response
    if _capture:
        _capture.capture_response(
            request_id=request_id,
            response=response_text,
            finish_reason=response.choices[0].finish_reason,
            usage={"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens}
        )
    
    # Extract JSON from response (handle extra text)
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        data = _extract_first_json_object(response_text)
    
    return validate_review(data)
