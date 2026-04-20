import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AISettings:
    """Runtime settings for the external LLM provider."""

    provider: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 30

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    @classmethod
    def from_env(cls) -> "AISettings":
        """Load provider settings from environment variables.

        Default setup targets DeepSeek because the current client uses an
        OpenAI-compatible chat completions API.
        """
        return cls(
            provider=os.getenv("TASK_AI_PROVIDER", "deepseek").strip() or "deepseek",
            base_url=os.getenv("TASK_AI_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            api_key=os.getenv("TASK_AI_API_KEY", os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENAI_API_KEY", ""))).strip(),
            model=os.getenv("TASK_AI_MODEL", "deepseek-reasoner").strip() or "deepseek-reasoner",
            timeout_seconds=int(os.getenv("TASK_AI_TIMEOUT", "30")),
        )
