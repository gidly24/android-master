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

        Prefer OpenAI when an OpenAI key is available, otherwise fall back to
        DeepSeek. Both are used through an OpenAI-compatible API surface.
        """
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        default_provider = "openai" if openai_key else "deepseek"
        provider = os.getenv("TASK_AI_PROVIDER", default_provider).strip() or default_provider

        if provider == "openai":
            base_url = os.getenv("TASK_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            api_key = os.getenv("TASK_AI_API_KEY", openai_key).strip()
            model = os.getenv("TASK_AI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"
        else:
            base_url = os.getenv("TASK_AI_BASE_URL", "https://api.deepseek.com").rstrip("/")
            api_key = os.getenv("TASK_AI_API_KEY", deepseek_key or openai_key).strip()
            model = os.getenv("TASK_AI_MODEL", "deepseek-reasoner").strip() or "deepseek-reasoner"

        return cls(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=int(os.getenv("TASK_AI_TIMEOUT", "45")),
        )
