import json
import logging
import os

from openai import AsyncOpenAI, BadRequestError, NotFoundError

from app.prompts import ARCHITECT_PROMPT, build_agent_user_prompt
from app.schemas import REVIEW_SCHEMA, validate_review

_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
_logger = logging.getLogger(__name__)

# Global capture instance (will be set by batch reviewer)
_capture = None


def set_api_capture(capture_instance):
    """Set the API capture instance to use."""
    global _capture
    _capture = capture_instance


async def run_openai_architect(
    review_context: dict,
    previous_reviews: list[dict],
    round_number: int,
) -> dict:
    model = os.getenv("OPENAI_MODEL", "gpt-5.1-codex-mini")
    user_content = build_agent_user_prompt(review_context, previous_reviews, round_number)
    
    # Capture the request
    request_id = None
    if _capture:
        request_id = _capture.capture_request(
            provider="openai",
            model=model,
            system_prompt=ARCHITECT_PROMPT,
            user_message=user_content,
            metadata={"round": round_number, "pr": review_context.get("pr_number")}
        )

    try:
        # Try standard chat completions (fails for some non-chat models)
        response = await _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ARCHITECT_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "code_review",
                    "strict": False,
                    "schema": REVIEW_SCHEMA,
                },
            },
        )
        data = json.loads(response.choices[0].message.content)

        if _capture:
            _capture.capture_response(
                request_id=request_id,
                response=response.choices[0].message.content,
                finish_reason=response.choices[0].finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            )
    except (NotFoundError, BadRequestError):
        response = await _client.responses.create(
            model=model,
            instructions=ARCHITECT_PROMPT,
            input=user_content,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "code_review",
                    "schema": REVIEW_SCHEMA,
                    "strict": False,
                }
            },
        )
        # The v1/responses API returns output differently; extract first text block.
        output_text = None
        if hasattr(response, "output") and response.output and len(response.output) > 0:
            first_output = response.output[0]
            if (
                hasattr(first_output, "content")
                and first_output.content
                and len(first_output.content) > 0
            ):
                output_text = getattr(first_output.content[0], "text", None)

        if not output_text and hasattr(response, "output") and hasattr(response.output, "__iter__"):
            for out in response.output:
                if hasattr(out, "content") and hasattr(out.content, "__iter__"):
                    for content_part in out.content:
                        if hasattr(content_part, "text"):
                            output_text = content_part.text
                            break

        if not isinstance(output_text, str):
            _logger.error("Failed to extract text from Responses API output")
            raise ValueError("Failed to extract JSON string from Responses API output")

        data = json.loads(output_text)

        if _capture:
            _capture.capture_response(
                request_id=request_id,
                response=output_text,
                finish_reason="stop",
            )

    return validate_review(data)
