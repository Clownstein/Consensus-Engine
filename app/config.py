import os
from functools import cached_property

from dotenv import load_dotenv

load_dotenv()


class Config:
    @cached_property
    def openai_api_key(self) -> str:
        return os.environ["OPENAI_API_KEY"]

    @cached_property
    def anthropic_api_key(self) -> str:
        return os.environ["ANTHROPIC_API_KEY"]

    @cached_property
    def gemini_api_key(self) -> str:
        return os.environ["GEMINI_API_KEY"]

    @cached_property
    def github_app_id(self) -> str:
        return os.environ["GITHUB_APP_ID"]

    @cached_property
    def github_private_key_path(self) -> str:
        return os.environ["GITHUB_PRIVATE_KEY_PATH"]

    @cached_property
    def github_webhook_secret(self) -> str:
        return os.environ["GITHUB_WEBHOOK_SECRET"]

    @property
    def openai_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o")

    @property
    def anthropic_model(self) -> str:
        return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    @property
    def gemini_model(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    @property
    def max_debate_rounds(self) -> int:
        return int(os.getenv("MAX_DEBATE_ROUNDS", "3"))

    @property
    def min_confidence_to_approve(self) -> float:
        return float(os.getenv("MIN_CONFIDENCE_TO_APPROVE", "0.80"))

    max_files_per_review: int = 50
    max_diff_bytes: int = 180_000


config = Config()
