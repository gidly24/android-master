from __future__ import annotations

from typing import Any, Optional

from ai_agent import TaskAIAgent
from ai_config import AISettings


class _NLUStubTaskService:
    """Minimal task service stub for parsing-only flows."""


def parse_user_message(text: str, history: Optional[list[dict[str, str]]] = None) -> dict[str, Any]:
    """
    Parse a user phrase into structured action/data payload.

    External LLM usage is disabled intentionally to keep tests deterministic.
    """
    settings = AISettings(
        provider="openai",
        base_url="",
        api_key="",
        model="",
        timeout_seconds=1,
    )
    agent = TaskAIAgent(task_service=_NLUStubTaskService(), settings=settings, client=None)
    command = agent.analyze_message(text=text, history=history or [])
    return {
        "action": command.action,
        "data": dict(command.data or {}),
        "answer": command.answer,
    }

