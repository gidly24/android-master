import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ai_config import AISettings
from ai_date_parser import build_relative_date_hints, extract_time, parse_relative_datetime


ALLOWED_ACTIONS = {
    "create_task",
    "delete_task",
    "mark_as_done",
    "update_task",
    "list_tasks",
    "get_statistics",
    "back_to_menu",
    "clarify",
}

ALLOWED_CATEGORIES = {"лекарства", "платежи", "бытовые дела", "подписки", "другое"}
ALLOWED_RECURRENCE = {None, "ежедневно", "еженедельно", "ежемесячно"}
ALLOWED_PRIORITIES = {1, 2, 3}


@dataclass
class AgentCommand:
    action: str
    data: dict[str, Any] = field(default_factory=dict)
    answer: str = ""


@dataclass
class AssistantReply:
    action: str
    data: dict[str, Any]
    answer: str
    should_refresh: bool = False
    ui_hints: dict[str, Any] = field(default_factory=dict)


class BaseLLMClient:
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class OpenAIClient(BaseLLMClient):
    """OpenAI-compatible client that targets /chat/completions.

    Used for DeepSeek by default because DeepSeek exposes a compatible API.
    """

    def __init__(self, settings: AISettings):
        self.settings = settings

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.settings.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = urllib.request.Request(
            url=f"{self.settings.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"LLM HTTP error: {error.code} {detail}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"LLM connection error: {error.reason}") from error

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("LLM returned an unexpected response payload.") from error
        if isinstance(content, list):
            text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
            return "".join(text_parts)
        return content


class TaskCommandDispatcher:
    MAIN_MENU_BUTTONS = [
        {"label": "Создать", "message": "добавь задачу"},
        {"label": "Показать актуальные", "message": "покажи актуальные задачи"},
        {"label": "Удалить", "message": "удали задачу"},
        {"label": "Изменить", "message": "измени задачу"},
        {"label": "Выполнить", "message": "выполнить"},
        {"label": "Статистика", "message": "сколько у меня просроченных дел?"},
    ]

    def __init__(self, task_service):
        self.task_service = task_service

    def dispatch(self, command: AgentCommand) -> AssistantReply:
        action = command.action
        data = command.data or {}

        if action == "clarify":
            reply = AssistantReply(action=action, data=data, answer=command.answer or "Уточни, пожалуйста.", should_refresh=False)
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        if action == "back_to_menu":
            reply = AssistantReply(
                action="back_to_menu",
                data={},
                answer="Что дальше сделать?",
                should_refresh=False,
            )
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        if action == "create_task":
            try:
                result = self.task_service.create_task_from_ai(data)
            except ValueError as error:
                reply = AssistantReply(action="clarify", data={"reason": "validation_error"}, answer=str(error), should_refresh=False)
                reply.ui_hints = self._build_ui_hints(reply)
                return reply
            reply = AssistantReply(
                action="back_to_menu",
                data=result,
                answer=result.get("answer", command.answer or "Готово, добавил задачу."),
                should_refresh=True,
            )
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        if action == "delete_task":
            result = self.task_service.delete_task_from_ai(data)
            reply = AssistantReply(
                action="back_to_menu" if result.get("deleted") else result.get("action", action),
                data=result,
                answer=result.get("answer", command.answer or "Готово, удалил задачу."),
                should_refresh=result.get("deleted", False),
            )
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        if action == "mark_as_done":
            result = self.task_service.mark_task_done_from_ai(data)
            reply = AssistantReply(
                action="back_to_menu" if result.get("completed") else result.get("action", action),
                data=result,
                answer=result.get("answer", command.answer or "Готово, отметил задачу как выполненную."),
                should_refresh=result.get("completed", False),
            )
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        if action == "update_task":
            try:
                result = self.task_service.update_task_from_ai(data)
            except ValueError as error:
                reply = AssistantReply(action="clarify", data={"reason": "validation_error"}, answer=str(error), should_refresh=False)
                reply.ui_hints = self._build_ui_hints(reply)
                return reply
            reply = AssistantReply(
                action="back_to_menu" if result.get("updated") else result.get("action", action),
                data=result,
                answer=result.get("answer", command.answer or "Готово, обновил задачу."),
                should_refresh=result.get("updated", False),
            )
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        if action == "list_tasks":
            result = self.task_service.list_tasks_for_ai(data)
            reply = AssistantReply(
                action="back_to_menu",
                data=result,
                answer=result.get("answer", command.answer or "Подготовил список задач."),
                should_refresh=False,
            )
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        if action == "get_statistics":
            result = self.task_service.get_statistics_for_ai()
            reply = AssistantReply(
                action="back_to_menu",
                data=result,
                answer=result.get("answer", command.answer or "Подготовил статистику."),
                should_refresh=False,
            )
            reply.ui_hints = self._build_ui_hints(reply)
            return reply

        reply = AssistantReply(
            action="clarify",
            data={"reason": "unsupported_action"},
            answer="Не получилось распознать команду. Попробуй сформулировать иначе.",
            should_refresh=False,
        )
        reply.ui_hints = self._build_ui_hints(reply)
        return reply

    def _build_ui_hints(self, reply: AssistantReply) -> dict[str, Any]:
        buttons: list[dict[str, str]] = []
        data = reply.data or {}

        if reply.action == "clarify" and data.get("pending_action") == "create_task":
            missing_field = data.get("missing_field")
            if missing_field == "due_date_choice":
                buttons.extend(
                    [
                        {"label": "Поставить дату", "message": "/set_due_date"},
                        {"label": "Без даты", "message": "/skip_due_date"},
                    ]
                )
            elif missing_field == "time_choice":
                buttons.extend(
                    [
                        {"label": "Указать время", "message": "/set_time"},
                        {"label": "Без времени", "message": "/skip_time"},
                    ]
                )
            elif missing_field == "time":
                buttons.extend(
                    [
                        {"label": "18:00", "message": "18:00"},
                        {"label": "19:00", "message": "19:00"},
                        {"label": "09:00", "message": "09:00"},
                    ]
                )
            elif missing_field == "priority":
                buttons.extend(
                    [
                        {"label": "Низкий", "message": "/priority_1"},
                        {"label": "Средний", "message": "/priority_2"},
                        {"label": "Высокий", "message": "/priority_3"},
                    ]
                )
            elif missing_field == "due_date":
                buttons.extend(
                    [
                        {"label": "Завтра 18:00", "message": "завтра в 18:00"},
                        {"label": "Послезавтра 09:00", "message": "послезавтра в 09:00"},
                        {"label": "Через неделю", "message": "через неделю"},
                    ]
                )
        elif reply.action == "clarify" and data.get("candidates"):
            for index, candidate in enumerate(data["candidates"][:5], start=1):
                buttons.append(
                    {
                        "label": f"{index}. {candidate['title']}",
                        "message": str(index),
                    }
                )
            buttons.append({"label": "Назад", "message": "/back_to_menu"})
        elif reply.action == "create_task":
            title = data.get("title", "задачу")
            buttons.extend(
                [
                    {"label": "Изменить", "message": f"измени {title.lower()}"},
                    {"label": "Выполнить", "message": f"отметь {title.lower()} как выполненную"},
                    {"label": "Показать задачи", "message": "покажи все задачи"},
                ]
            )
        elif reply.action == "back_to_menu":
            buttons.extend(self.MAIN_MENU_BUTTONS)
        elif reply.action == "delete_task":
            buttons.extend(
                [
                    {"label": "Показать задачи", "message": "покажи все задачи"},
                    {"label": "Удалить еще", "message": "удали задачу"},
                ]
            )
        elif reply.action == "mark_as_done":
            buttons.extend(
                [
                    {"label": "Показать активные", "message": "покажи активные задачи"},
                    {"label": "Отметить еще", "message": "отметь задачу как выполненную"},
                ]
            )
        elif reply.action == "update_task":
            buttons.extend(
                [
                    {"label": "Перенести еще", "message": "измени задачу"},
                    {"label": "Показать задачи", "message": "покажи все задачи"},
                ]
            )
        elif reply.action == "list_tasks":
            buttons.extend(
                [
                    {"label": "Просроченные", "message": "покажи просроченные задачи"},
                    {"label": "На этой неделе", "message": "покажи задачи на этой неделе"},
                    {"label": "Статистика", "message": "сколько у меня просроченных дел?"},
                ]
            )
        elif reply.action == "get_statistics":
            buttons.extend(
                [
                    {"label": "Показать задачи", "message": "покажи все задачи"},
                    {"label": "Удалить задачу", "message": "удали задачу"},
                    {"label": "Создать задачу", "message": "добавь задачу"},
                ]
            )
        else:
            buttons.extend(self.MAIN_MENU_BUTTONS)

        return {"buttons": buttons}


class TaskAIAgent:
    SYSTEM_PROMPT = """Ты — интеллектуальный ассистент приложения для управления задачами.
Твоя задача — превращать естественные русские фразы пользователя в структурированные действия для task manager.

Доступные действия:
- create_task
- delete_task
- mark_as_done
- update_task
- list_tasks
- get_statistics
- clarify

Категории строго:
- лекарства
- платежи
- бытовые дела
- подписки
- другое

Правила:
- Всегда анализируй смысл фразы.
- Если пользователь использует относительные даты, преобразуй их в точную дату и время.
- Если точной даты нет, но ее можно разумно вывести из фразы — выведи.
- Если вывести нельзя — верни action=clarify.
- Если категория не подходит, выбирай "другое".
- Приоритет определи по контексту.
- Платежи обычно имеют высокий приоритет.
- Повторяющиеся задачи распознавай по словам: каждый день, каждую неделю, каждый месяц, ежедневно, еженедельно, ежемесячно.
- Отвечай строго валидным JSON без пояснений вне JSON.
- Для create_task поле due_date возвращай в формате YYYY-MM-DD HH:MM.
- Для update_task передавай task_id, если он известен; иначе title_query и только те поля, которые нужно изменить.
- Для list_tasks можешь передавать category, status, title_query, start_date, end_date.
- Для delete_task и mark_as_done передавай title_query и, если есть, task_id.
- Если пользователь пишет о будущем событии как о личном плане или намерении, это можно трактовать как create_task/напоминание, если фраза похожа на то, что человек хочет не забыть.
- Если сомневаешься, лучше верни clarify, чем выдумывай данные.
"""

    def __init__(self, task_service, settings: Optional[AISettings] = None, client: Optional[BaseLLMClient] = None):
        self.settings = settings or AISettings.from_env()
        self.client = client or (OpenAIClient(self.settings) if self.settings.is_configured else None)
        self.dispatcher = TaskCommandDispatcher(task_service)
        self.pending_resolution: Optional[dict[str, Any]] = None
        self.wizard_state: Optional[dict[str, Any]] = None

    def process_message(self, message: str, history: Optional[list[dict[str, str]]] = None) -> AssistantReply:
        if message.strip().lower() == "/back_to_menu":
            self.pending_resolution = None
            self.wizard_state = None
            return self.dispatcher.dispatch(AgentCommand(action="back_to_menu"))

        wizard_reply = self._handle_active_wizard(message)
        if wizard_reply is not None:
            return wizard_reply

        pending_reply = self._try_resolve_pending(message)
        if pending_reply is not None:
            return pending_reply
        command = self.analyze_message(message, history=history or [])
        if command.action == "create_task":
            return self._start_create_wizard(command.data)
        if command.action == "update_task" and not self._has_update_changes(command.data):
            return self._begin_update_flow(command.data)
        if command.action == "clarify" and command.data.get("pending_action") == "create_task":
            return self._start_create_wizard(command.data.get("payload", {}), start_step=command.data.get("missing_field", "title"))
        reply = self.dispatcher.dispatch(command)
        self._remember_pending_resolution(reply)
        return reply

    def analyze_message(self, message: str, history: Optional[list[dict[str, str]]] = None) -> AgentCommand:
        text = (message or "").strip()
        if not text:
            return AgentCommand(
                action="clarify",
                data={"missing_field": "message"},
                answer="Напиши, что нужно сделать с задачами.",
            )

        if self.client is not None:
            try:
                prompt = self._build_user_prompt(text, history or [])
                raw_response = self.client.complete(self.SYSTEM_PROMPT, prompt)
                return self._parse_llm_command(raw_response)
            except Exception:
                pass

        return self._heuristic_command(text)

    def _build_user_prompt(self, message: str, history: list[dict[str, str]]) -> str:
        now = datetime.now()
        recent_history = history[-6:]
        history_block = "\n".join(
            f"{item.get('role', 'user')}: {item.get('content', '').strip()}"
            for item in recent_history
            if item.get("content")
        )
        date_hints = build_relative_date_hints(message, now)
        return (
            f"{date_hints}\n\n"
            f"История диалога:\n{history_block or 'история пуста'}\n\n"
            f"Текущая пользовательская фраза:\n{message}\n\n"
            "Верни только JSON."
        )

    def _parse_llm_command(self, raw_response: str) -> AgentCommand:
        payload = self._load_json_payload(raw_response)
        return self._sanitize_command(payload)

    @staticmethod
    def _load_json_payload(raw_response: str) -> dict[str, Any]:
        cleaned = (raw_response or "").strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

    def _sanitize_command(self, payload: dict[str, Any]) -> AgentCommand:
        action = str(payload.get("action", "clarify")).strip()
        if action not in ALLOWED_ACTIONS:
            action = "clarify"

        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        answer = str(payload.get("answer", "")).strip()

        if action == "create_task":
            data = self._sanitize_create_data(data)
            if not data.get("title"):
                return AgentCommand("clarify", {"missing_field": "title", "pending_action": "create_task", "payload": data}, answer or "Как назвать задачу?")
        if action == "update_task":
            if not data.get("task_id") and not data.get("title_query"):
                return AgentCommand("clarify", {"missing_field": "title"}, answer or "Какую задачу изменить?")

        return AgentCommand(action=action, data=data, answer=answer)

    @staticmethod
    def _sanitize_create_data(data: dict[str, Any]) -> dict[str, Any]:
        category = str(data.get("category", "другое")).strip().lower()
        if category not in ALLOWED_CATEGORIES:
            category = "другое"

        recurrence = data.get("recurrence")
        recurrence = str(recurrence).strip().lower() if recurrence else None
        if recurrence not in ALLOWED_RECURRENCE:
            recurrence = None

        priority = data.get("priority", 2)
        try:
            priority = int(priority)
        except (TypeError, ValueError):
            priority = 2
        if priority not in ALLOWED_PRIORITIES:
            priority = 2

        due_date = str(data.get("due_date", "")).strip()
        if due_date:
            due_date = TaskAIAgent._normalize_due_date_string(due_date)

        return {
            "title": str(data.get("title", "")).strip(),
            "description": str(data.get("description", "Создано через ИИ-чат")).strip() or "Создано через ИИ-чат",
            "category": category,
            "due_date": due_date,
            "recurrence": recurrence,
            "priority": priority,
        }

    @staticmethod
    def _normalize_due_date_string(value: str) -> str:
        normalized = value.replace("T", " ").strip()
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(normalized, fmt)
                if fmt == "%Y-%m-%d":
                    parsed = parsed.replace(hour=23, minute=59)
                return parsed.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                continue
        return normalized

    def _heuristic_command(self, message: str) -> AgentCommand:
        text = message.strip()
        lowered = text.lower()

        if "сколько" in lowered and "просроч" in lowered:
            return AgentCommand("get_statistics", {}, "Сейчас посчитаю просроченные дела.")

        if any(word in lowered for word in ("покажи", "список", "какие", "выведи")):
            filters: dict[str, Any] = {}
            category = self._infer_category(lowered)
            if category != "другое" or "другое" in lowered:
                filters["category"] = category
            date_context = parse_relative_datetime(lowered, datetime.now())
            if date_context.start_date:
                filters["start_date"] = date_context.start_date.isoformat()
            if date_context.end_date:
                filters["end_date"] = date_context.end_date.isoformat()
            if "просроч" in lowered:
                filters["status"] = "просрочена"
            if "все" in lowered and "актуаль" not in lowered:
                filters["view"] = "actual"
            return AgentCommand("list_tasks", filters, "Сейчас покажу подходящие задачи.")

        if any(word in lowered for word in ("отметь", "заверши", "выполнил", "выполненной", "выполненным", "выполнить")):
            title_query = self._extract_title_query_for_action(text)
            if not title_query:
                return AgentCommand("mark_as_done", {"title_query": ""}, "Сейчас помогу отметить задачу.")
            return AgentCommand("mark_as_done", {"title_query": title_query}, "Отмечаю задачу как выполненную.")

        if any(word in lowered for word in ("удали", "удалить", "сотри")):
            title_query = self._extract_title_query_for_action(text)
            if not title_query:
                return AgentCommand("delete_task", {"title_query": ""}, "Сейчас помогу удалить задачу.")
            return AgentCommand("delete_task", {"title_query": title_query}, "Сейчас удалю задачу.")

        if any(word in lowered for word in ("измени", "поменяй", "обнови", "перенеси", "исправь", "редактируй")):
            return self._heuristic_update_command(text, lowered)

        explicit_create = any(
            word in lowered
            for word in ("добавь", "добавить", "запиши", "записать", "создай", "создать", "поставь", "поставить")
        )
        if explicit_create or self._looks_like_implicit_task(lowered):
            parsed = parse_relative_datetime(lowered, datetime.now())
            if (
                not explicit_create
                and parsed.due_at is None
                and not any(word in lowered for word in ("каждый", "ежедневно", "еженедельно", "ежемесячно"))
            ):
                return AgentCommand("clarify", {"missing_field": "due_date"}, "Не до конца понял дату, уточни пожалуйста.")

            category = self._infer_category(lowered)
            title = self._infer_title(text, category)
            recurrence = self._infer_recurrence(lowered)
            priority = 3 if category == "платежи" else 2
            description = self._infer_description(text)
            due_at = parsed.due_at
            if recurrence and due_at is None:
                due_at = datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)
            due_date = due_at.strftime("%Y-%m-%d %H:%M") if due_at else ""

            if title.lower() in {"задача", "новая задача", "добавь задачу"}:
                return AgentCommand(
                    "clarify",
                    {
                        "missing_field": "title",
                        "pending_action": "create_task",
                        "payload": {
                            "description": description,
                            "category": category,
                            "due_date": due_date,
                            "recurrence": recurrence,
                            "priority": priority,
                        },
                    },
                    "Как назвать задачу?",
                )

            payload = {
                "title": title,
                "description": description,
                "category": category,
                "due_date": due_date,
                "recurrence": recurrence,
                "priority": priority,
            }
            if due_date:
                if parsed.has_explicit_time:
                    return AgentCommand(
                        "clarify",
                        {
                            "missing_field": "priority",
                            "pending_action": "create_task",
                            "payload": payload,
                        },
                        f"Понял задачу «{title}». Осталось выбрать приоритет.",
                    )
                return AgentCommand(
                    "clarify",
                    {
                        "missing_field": "time_choice",
                        "pending_action": "create_task",
                        "payload": payload,
                    },
                    f"Для задачи «{title}» дата есть. Добавить точное время или оставить без времени?",
                )
            return AgentCommand(
                "clarify",
                {
                    "missing_field": "due_date_choice",
                    "pending_action": "create_task",
                    "payload": payload,
                },
                f"Понял задачу «{title}». Поставить дату и время или оставить без даты?",
            )

        return AgentCommand("clarify", {"missing_field": "intent"}, "Не до конца понял запрос. Напиши, что нужно сделать.")

    @staticmethod
    def _extract_title_query_for_action(text: str) -> str:
        lowered = text.lower()
        patterns = [
            r"(?:отметь|удали|удалить)\s+(.+?)(?:\s+как\s+выполн\w+)?$",
            r"(?:заверши)\s+(.+)$",
            r"(?:измени|поменяй|обнови|редактируй)\s+(.+?)(?:\s+на\s+.+)?$",
            r"(?:перенеси)\s+(.+?)(?:\s+на\s+.+)?$",
        ]
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                result = match.group(1).strip(" .!?\"'")
                if result in {"задачу", "дело", "напоминание", "задача"}:
                    return ""
                return result
        return ""

    @staticmethod
    def _infer_recurrence(text: str) -> Optional[str]:
        if "каждый день" in text or "ежедневно" in text:
            return "ежедневно"
        if "каждую неделю" in text or "еженедельно" in text:
            return "еженедельно"
        if "каждый месяц" in text or "ежемесячно" in text:
            return "ежемесячно"
        return None

    @staticmethod
    def _infer_category(text: str) -> str:
        if any(word in text for word in ("таблет", "врач", "анализ", "укол", "лекар")):
            return "лекарства"
        if any(word in text for word in ("оплат", "счет", "счёт", "интернет", "аренд", "квартплат", "жкх")):
            return "платежи"
        if any(
            word in text
            for word in (
                "подписк",
                "spotify",
                "netflix",
                "youtube premium",
                "youtube",
                "watch tv",
                "tv",
                "телевиз",
                "сериал",
                "фильм",
                "кинопоиск",
                "okko",
                "ivi",
                "wink",
                "яндекс плюс",
                "музыка",
                "стриминг",
            )
        ):
            return "подписки"
        if any(word in text for word in ("уборк", "стирк", "магазин", "мусор", "продукт", "быт")):
            return "бытовые дела"
        return "другое"

    @staticmethod
    def _infer_title(text: str, category: str) -> str:
        lowered = text.lower()
        if "трениров" in lowered:
            return "Тренировка"
        if "поеду" in lowered or "поездк" in lowered:
            city_match = re.search(r"\bв\s+([а-яё\-]+)\b", lowered)
            if city_match:
                city = TaskAIAgent._normalize_named_phrase(city_match.group(1))
                return f"Поездка в {city}"
            return "Поездка"
        if re.search(r"\bбан(?:я|ю|е)\b", lowered) and ("сходить" in lowered or "поход" in lowered):
            return "Поход в баню"
        if category == "платежи" and "интернет" in lowered:
            return "Оплата интернета"
        if category == "лекарства" and "витамин" in lowered:
            return "Принять витамины"
        if any(word in lowered for word in ("watch tv", "телевиз", " tv", "tv ")):
            return "Посмотреть ТВ"
        if any(word in lowered for word in ("сериал", "series")):
            return "Посмотреть сериал"
        if any(word in lowered for word in ("фильм", "movie")):
            return "Посмотреть фильм"
        if "youtube" in lowered:
            return "Посмотреть YouTube"
        phrase = TaskAIAgent._strip_task_noise(text)
        if not phrase:
            return "Новая задача"

        pattern_builders = [
            (r"\b(?:сходить|съездить)\s+в\s+(.+)", lambda m: f"Поход в {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\b(?:поехать|поеду)\s+в\s+(.+)", lambda m: f"Поездка в {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\b(?:оплатить|заплатить(?:\s+за)?)\s+(.+)", lambda m: f"Оплата {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bзаписаться\s+на\s+(.+)", lambda m: f"Запись на {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bзаписаться\s+к\s+(.+)", lambda m: f"Запись к {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bпозвонить\s+(.+)", lambda m: f"Позвонить {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bнаписать\s+(.+)", lambda m: f"Написать {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bкупить\s+(.+)", lambda m: f"Купить {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bзаказать\s+(.+)", lambda m: f"Заказать {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bвынести\s+(.+)", lambda m: f"Вынести {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bубрать\s+(.+)", lambda m: f"Убрать {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bпомыть\s+(.+)", lambda m: f"Помыть {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bпосмотреть\s+(.+)", lambda m: f"Посмотреть {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
            (r"\bпрочитать\s+(.+)", lambda m: f"Прочитать {TaskAIAgent._normalize_named_phrase(m.group(1))}"),
        ]
        for pattern, builder in pattern_builders:
            match = re.search(pattern, phrase)
            if match:
                title = builder(match)
                return TaskAIAgent._cleanup_title(title)

        if phrase.lower() in {"задача", "задачу", "напоминание", "дело"}:
            return "Новая задача"
        return TaskAIAgent._cleanup_title(phrase)

    @staticmethod
    def _infer_description(text: str) -> str:
        money = re.search(r"(\d[\d\s]*)\s*руб", text.lower())
        if money:
            amount = re.sub(r"\s+", "", money.group(1))
            return f"Создано через ИИ-чат. Сумма: {amount} рублей."
        return "Создано через ИИ-чат"

    def _heuristic_update_command(self, text: str, lowered: str) -> AgentCommand:
        title_query = self._extract_title_query_for_action(text)
        data: dict[str, Any] = {"title_query": title_query}

        date_context = parse_relative_datetime(lowered, datetime.now())
        if date_context.due_at is not None:
            data["due_date"] = date_context.due_at.strftime("%Y-%m-%d %H:%M")

        priority_match = re.search(r"\b(высок(?:ий|им)?|средн(?:ий|им)?|низк(?:ий|им)?)\b", lowered)
        if priority_match:
            mapping = {"высок": 3, "средн": 2, "низк": 1}
            for prefix, value in mapping.items():
                if priority_match.group(1).startswith(prefix):
                    data["priority"] = value
                    break

        category = self._infer_category(lowered)
        if category != "другое":
            data["category"] = category

        if not title_query:
            return AgentCommand("update_task", data, "Уточню, какую задачу нужно изменить.")
        return AgentCommand("update_task", data, "Сейчас обновлю задачу.")

    @staticmethod
    def _has_update_changes(data: dict[str, Any]) -> bool:
        editable_fields = ("title", "description", "category", "due_date", "recurrence", "priority", "clear_due_date")
        for field in editable_fields:
            if field == "clear_due_date" and data.get(field):
                return True
            value = data.get(field)
            if value not in (None, ""):
                return True
        return False

    @staticmethod
    def _looks_like_implicit_task(text: str) -> bool:
        future_markers = (
            "через ",
            "завтра",
            "послезавтра",
            "сегодня",
            "в пятниц",
            "в понедель",
            "в вторник",
            "в сред",
            "в четверг",
            "в суббот",
            "в воскрес",
            "на следующей неделе",
            "на этой неделе",
        )
        intent_markers = (
            "поеду",
            "нужно",
            "надо",
            "буду",
            "не забыть",
            "напомни",
            "встреча",
            "поездка",
            "сходить",
            "оплата",
            "запись",
        )
        return any(marker in text for marker in future_markers) and any(marker in text for marker in intent_markers)

    def _remember_pending_resolution(self, reply: AssistantReply):
        data = reply.data or {}
        candidates = data.get("candidates")
        pending_action = data.get("pending_action")
        if reply.action != "clarify" or not pending_action:
            self.pending_resolution = None
            return

        self.pending_resolution = {
            "action": pending_action,
            "candidates": candidates or [],
            "payload": data.get("payload", {}),
            "missing_field": data.get("missing_field"),
        }

    def _try_resolve_pending(self, message: str) -> Optional[AssistantReply]:
        if not self.pending_resolution:
            return None

        if self._looks_like_new_command(message):
            self.pending_resolution = None
            return None

        if self.pending_resolution["action"] == "create_task" and self.pending_resolution.get("missing_field") == "title":
            payload = dict(self.pending_resolution.get("payload", {}))
            inferred_category = self._infer_category(message.strip().lower())
            payload["category"] = inferred_category
            payload["title"] = self._infer_title(message.strip(), inferred_category)
            self.pending_resolution = None
            reply = self._next_create_reply(payload)
            self._remember_pending_resolution(reply)
            return reply

        if self.pending_resolution["action"] == "create_task" and self.pending_resolution.get("missing_field") == "due_date_choice":
            payload = dict(self.pending_resolution.get("payload", {}))
            normalized = message.strip().lower()
            if normalized in {"/skip_due_date", "без даты", "оставить без даты"}:
                self.pending_resolution = None
                reply = self._build_priority_reply(payload)
                self._remember_pending_resolution(reply)
                return reply
            if normalized in {"/set_due_date", "поставить дату", "дата"}:
                self.pending_resolution = None
                reply = AssistantReply(
                    action="clarify",
                    data={
                        "pending_action": "create_task",
                        "missing_field": "due_date",
                        "payload": payload,
                    },
                    answer="Напиши дату и время в свободной форме. Например: завтра в 18:00 или через неделю в пятницу.",
                    should_refresh=False,
                )
                reply.ui_hints = self.dispatcher._build_ui_hints(reply)
                self._remember_pending_resolution(reply)
                return reply

        if self.pending_resolution["action"] == "create_task" and self.pending_resolution.get("missing_field") == "due_date":
            payload = dict(self.pending_resolution.get("payload", {}))
            parsed_due_date = self._parse_due_date_from_text(message)
            if parsed_due_date:
                payload["due_date"] = parsed_due_date
                self.pending_resolution = None
                if self._text_has_explicit_time(message):
                    reply = self._build_priority_reply(payload)
                else:
                    reply = self._build_time_choice_reply(payload)
                self._remember_pending_resolution(reply)
                return reply
            reply = AssistantReply(
                action="clarify",
                data={
                    "pending_action": "create_task",
                    "missing_field": "due_date",
                    "payload": payload,
                },
                answer="Не до конца понял дату. Попробуй, например: завтра в 18:00, послезавтра 09:30 или через неделю.",
                should_refresh=False,
            )
            reply.ui_hints = self.dispatcher._build_ui_hints(reply)
            self._remember_pending_resolution(reply)
            return reply

        if self.pending_resolution["action"] == "create_task" and self.pending_resolution.get("missing_field") == "time_choice":
            payload = dict(self.pending_resolution.get("payload", {}))
            normalized = message.strip().lower()
            if normalized in {"/skip_time", "без времени", "оставить без времени"}:
                if payload.get("due_date"):
                    payload["due_date"] = self._normalize_due_without_time(payload["due_date"])
                self.pending_resolution = None
                reply = self._build_priority_reply(payload)
                self._remember_pending_resolution(reply)
                return reply
            if normalized in {"/set_time", "указать время", "добавить время"}:
                self.pending_resolution = None
                reply = AssistantReply(
                    action="clarify",
                    data={
                        "pending_action": "create_task",
                        "missing_field": "time",
                        "payload": payload,
                    },
                    answer="Напиши время в свободной форме. Например: 18:00, 18-00 или 7 часов.",
                    should_refresh=False,
                )
                reply.ui_hints = self.dispatcher._build_ui_hints(reply)
                self._remember_pending_resolution(reply)
                return reply

        if self.pending_resolution["action"] == "create_task" and self.pending_resolution.get("missing_field") == "time":
            payload = dict(self.pending_resolution.get("payload", {}))
            parsed_time = self._parse_time_from_text(message)
            if parsed_time is not None and payload.get("due_date"):
                payload["due_date"] = self._apply_time_to_due_date(payload["due_date"], parsed_time)
                self.pending_resolution = None
                reply = self._build_priority_reply(payload)
                self._remember_pending_resolution(reply)
                return reply
            reply = AssistantReply(
                action="clarify",
                data={
                    "pending_action": "create_task",
                    "missing_field": "time",
                    "payload": payload,
                },
                answer="Не до конца понял время. Попробуй так: 18:00, 18-00 или 7 часов.",
                should_refresh=False,
            )
            reply.ui_hints = self.dispatcher._build_ui_hints(reply)
            self._remember_pending_resolution(reply)
            return reply

        if self.pending_resolution["action"] == "create_task" and self.pending_resolution.get("missing_field") == "priority":
            payload = dict(self.pending_resolution.get("payload", {}))
            priority = self._parse_priority_from_text(message)
            if priority is not None:
                payload["priority"] = priority
                self.pending_resolution = None
                reply = self.dispatcher.dispatch(AgentCommand(action="create_task", data=payload))
                self._remember_pending_resolution(reply)
                return reply
            reply = AssistantReply(
                action="clarify",
                data={
                    "pending_action": "create_task",
                    "missing_field": "priority",
                    "payload": payload,
                },
                answer="Выбери приоритет: низкий, средний или высокий.",
                should_refresh=False,
            )
            reply.ui_hints = self.dispatcher._build_ui_hints(reply)
            self._remember_pending_resolution(reply)
            return reply

        selected = self._select_candidate_from_message(message, self.pending_resolution["candidates"])
        if not selected:
            candidate_lines = [
                f"{index + 1}. {candidate['title']}"
                for index, candidate in enumerate(self.pending_resolution["candidates"][:7])
            ]
            return AssistantReply(
                action="clarify",
                data={
                    "pending_action": self.pending_resolution["action"],
                    "candidates": self.pending_resolution["candidates"],
                    "payload": self.pending_resolution["payload"],
                    "missing_field": self.pending_resolution.get("missing_field"),
                },
                answer="Не понял, какую именно задачу выбрать.\n" + "\n".join(candidate_lines),
                should_refresh=False,
            )

        payload = dict(self.pending_resolution.get("payload", {}))
        action = self.pending_resolution["action"]
        payload["task_id"] = selected["id"]
        self.pending_resolution = None
        if action == "update_task" and not self._has_update_changes(payload):
            return self._start_update_wizard(int(selected["id"]), payload)
        reply = self.dispatcher.dispatch(AgentCommand(action=action, data=payload))
        self._remember_pending_resolution(reply)
        return reply

    @staticmethod
    def _select_candidate_from_message(message: str, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        lowered = message.lower().strip()
        ordinal_map = {
            "перв": 0,
            "втор": 1,
            "треть": 2,
            "четвер": 3,
            "пят": 4,
        }
        if lowered.isdigit():
            index = int(lowered) - 1
            if 0 <= index < len(candidates):
                return candidates[index]
        for stem, index in ordinal_map.items():
            if stem in lowered and 0 <= index < len(candidates):
                return candidates[index]
        for candidate in candidates:
            title = str(candidate.get("title", "")).lower()
            if lowered and (lowered in title or any(part in title for part in lowered.split() if len(part) > 2)):
                return candidate
        return None

    @staticmethod
    def _looks_like_new_command(message: str) -> bool:
        lowered = message.lower().strip()
        command_markers = (
            "добав",
            "запиш",
            "созда",
            "постав",
            "удал",
            "измени",
            "поменя",
            "обнови",
            "перенес",
            "покажи",
            "список",
            "сколько",
            "отмет",
            "выполн",
            "заверш",
        )
        return any(marker in lowered for marker in command_markers)

    def _handle_active_wizard(self, message: str) -> Optional[AssistantReply]:
        if not self.wizard_state:
            return None
        if self._looks_like_cancel_command(message):
            self.wizard_state = None
            return self._make_wizard_reply(
                answer="Окей, отменил текущий сценарий. Что дальше сделать?",
                buttons=TaskCommandDispatcher.MAIN_MENU_BUTTONS,
            )
        if self._looks_like_new_command(message):
            self.wizard_state = None
            return None

        if self.wizard_state.get("mode") == "create":
            return self._handle_create_wizard(message)
        if self.wizard_state.get("mode") == "update":
            return self._handle_update_wizard(message)
        return None

    def _begin_update_flow(self, payload: dict[str, Any]) -> AssistantReply:
        service = self.dispatcher.task_service
        task_id = payload.get("task_id")
        if task_id:
            return self._start_update_wizard(int(task_id), payload)

        active_tasks = service.get_tasks()
        if not active_tasks:
            return self.dispatcher.dispatch(
                AgentCommand(action="back_to_menu", data={}, answer="Активных задач сейчас нет.")
            )

        title_query = str(payload.get("title_query", "")).strip()
        if not title_query:
            reply = AssistantReply(
                action="clarify",
                data={
                    "pending_action": "update_task",
                    "candidates": [self._task_to_candidate(item) for item in active_tasks[:7]],
                    "payload": {},
                },
                answer=self._build_candidate_prompt(active_tasks[:7], "Какую задачу изменить?"),
                should_refresh=False,
            )
            reply.ui_hints = self.dispatcher._build_ui_hints(reply)
            self._remember_pending_resolution(reply)
            return reply

        matches = service.find_tasks_by_title(title_query)
        if not matches:
            reply = AssistantReply(
                action="clarify",
                data={
                    "pending_action": "update_task",
                    "candidates": [self._task_to_candidate(item) for item in active_tasks[:7]],
                    "payload": {},
                },
                answer="Не нашел подходящую задачу. Выбери одну из активных:",
                should_refresh=False,
            )
            reply.ui_hints = self.dispatcher._build_ui_hints(reply)
            self._remember_pending_resolution(reply)
            return reply

        if len(matches) > 1:
            reply = AssistantReply(
                action="clarify",
                data={
                    "pending_action": "update_task",
                    "candidates": [self._task_to_candidate(item) for item in matches[:7]],
                    "payload": {},
                },
                answer=self._build_candidate_prompt(matches[:7], "Какую задачу изменить?"),
                should_refresh=False,
            )
            reply.ui_hints = self.dispatcher._build_ui_hints(reply)
            self._remember_pending_resolution(reply)
            return reply

        return self._start_update_wizard(matches[0].id, payload)

    def _start_update_wizard(self, task_id: int, payload: Optional[dict[str, Any]] = None) -> AssistantReply:
        service = self.dispatcher.task_service
        task = service.get_task(int(task_id))
        if task is None:
            return self.dispatcher.dispatch(AgentCommand(action="back_to_menu", data={}, answer="Не нашел задачу для изменения."))

        draft = self._task_to_wizard_draft(task)
        original = dict(draft)
        payload = payload or {}
        if payload.get("title"):
            draft["title"] = self._cleanup_title(str(payload["title"]))
        if payload.get("category"):
            draft["category"] = str(payload["category"]).strip().lower()
        if payload.get("due_date"):
            draft["due_date"] = str(payload["due_date"]).strip()
        if payload.get("priority") not in (None, ""):
            try:
                draft["priority"] = int(payload["priority"])
            except (TypeError, ValueError):
                pass

        self.wizard_state = {
            "mode": "update",
            "step": "field_choice",
            "task_id": int(task_id),
            "draft": draft,
            "original": original,
        }
        return self._reply_for_update_step()

    def _start_create_wizard(self, payload: dict[str, Any], start_step: str | None = None) -> AssistantReply:
        draft = {
            "title": str(payload.get("title", "")).strip(),
            "description": str(payload.get("description", "Создано через ИИ-чат")).strip() or "Создано через ИИ-чат",
            "category": str(payload.get("category", "другое")).strip().lower() or "другое",
            "due_date": str(payload.get("due_date", "")).strip(),
            "recurrence": payload.get("recurrence"),
            "priority": int(payload.get("priority", 2)) if str(payload.get("priority", 2)).isdigit() else 2,
        }
        draft["title"] = self._cleanup_title(draft["title"]) if draft["title"] else ""

        if start_step == "title" or not draft["title"]:
            step = "title"
        elif draft["due_date"]:
            step = "time_choice" if not self._due_date_has_custom_time(draft["due_date"]) else "priority"
        else:
            step = "date_choice"

        self.wizard_state = {"mode": "create", "step": step, "draft": draft}
        return self._reply_for_create_step()

    def _handle_create_wizard(self, message: str) -> AssistantReply:
        assert self.wizard_state is not None
        draft = self.wizard_state["draft"]
        step = self.wizard_state["step"]
        normalized = message.strip().lower()

        if step == "title":
            inferred_category = self._infer_category(message.strip().lower())
            draft["category"] = inferred_category
            draft["title"] = self._infer_title(message.strip(), inferred_category)
            self.wizard_state["step"] = "date_choice"
            return self._reply_for_create_step()

        if step == "date_choice":
            if normalized in {"/skip_due_date", "без даты", "оставить без даты"}:
                draft["due_date"] = ""
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            if normalized in {"/quick_today", "сегодня"}:
                draft["due_date"] = self._parse_due_date_from_text("сегодня")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_create_step()
            if normalized in {"/quick_tomorrow", "завтра"}:
                draft["due_date"] = self._parse_due_date_from_text("завтра")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_create_step()
            if normalized in {"/quick_day_after_tomorrow", "послезавтра"}:
                draft["due_date"] = self._parse_due_date_from_text("послезавтра")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_create_step()
            if normalized in {"/quick_next_week", "через неделю"}:
                draft["due_date"] = self._parse_due_date_from_text("через неделю")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_create_step()
            if self._parse_due_date_from_text(message) or self._extract_month_only(message):
                self.wizard_state["step"] = "date_input"
                return self._handle_create_wizard(message)
            self.wizard_state["step"] = "date_input"
            return self._reply_for_create_step()

        if step == "date_input":
            due_date = self._parse_due_date_from_text(message)
            if due_date:
                draft["due_date"] = due_date
                self.wizard_state["step"] = "priority" if self._text_has_explicit_time(message) else "time_choice"
                return self._reply_for_create_step()
            month_only = self._extract_month_only(message)
            if month_only:
                month_label = self._month_to_genitive(month_only)
                return self._make_wizard_reply(
                    answer=f"Понял месяц: {month_only}. Какое число поставить?",
                    buttons=[
                        {"label": f"1 {month_label}", "message": f"1 {month_label}"},
                        {"label": f"15 {month_label}", "message": f"15 {month_label}"},
                        {"label": f"30 {month_label}", "message": f"30 {month_label}"},
                        {"label": "Назад", "message": "/back_to_menu"},
                    ],
                    status={"mode": "Создание задачи", "step": "Шаг 2 из 5: дата", "waiting": "Жду дату"},
                    draft=self._format_draft_preview(draft),
                )
            return self._reply_for_create_step(error_text="Не до конца понял дату. Напиши, например: завтра, послезавтра в 18:00 или через неделю.")

        if step == "time_choice":
            if normalized in {"/skip_time", "без времени", "оставить без времени"}:
                if draft.get("due_date"):
                    draft["due_date"] = self._normalize_due_without_time(draft["due_date"])
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            if normalized in {"/quick_0900", "09:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("09:00"))
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            if normalized in {"/quick_1200", "12:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("12:00"))
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            if normalized in {"/quick_1800", "18:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("18:00"))
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            if normalized in {"/quick_2000", "20:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("20:00"))
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            self.wizard_state["step"] = "time_input"
            return self._reply_for_create_step()

        if step == "time_input":
            parsed_time = self._parse_time_from_text(message)
            if parsed_time is not None:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], parsed_time)
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            return self._reply_for_create_step(error_text="Не до конца понял время. Напиши, например: 18:00, 18-00 или 7 часов.")

        if step == "priority":
            priority = self._parse_priority_from_text(message)
            if priority is not None:
                draft["priority"] = priority
                self.wizard_state["step"] = "confirm"
                return self._reply_for_create_step()
            return self._reply_for_create_step(error_text="Выбери приоритет: низкий, средний или высокий.")

        if step == "confirm":
            if normalized in {"/confirm_create", "создать", "сохранить"}:
                self.wizard_state = None
                reply = self.dispatcher.dispatch(AgentCommand(action="create_task", data=draft))
                self._remember_pending_resolution(reply)
                return reply
            if normalized in {"/edit_date", "дата"}:
                self.wizard_state["step"] = "date_choice"
                return self._reply_for_create_step()
            if normalized in {"/edit_time", "время"}:
                if draft.get("due_date"):
                    self.wizard_state["step"] = "time_choice"
                else:
                    self.wizard_state["step"] = "date_choice"
                return self._reply_for_create_step()
            if normalized in {"/edit_priority", "приоритет"}:
                self.wizard_state["step"] = "priority"
                return self._reply_for_create_step()
            if normalized in {"/edit_title", "название"}:
                self.wizard_state["step"] = "title"
                return self._reply_for_create_step()
            return self._reply_for_create_step(error_text="Нажми «Создать» или выбери, что изменить.")

        return self._make_wizard_reply(answer="Не понял текущий шаг. Давай попробуем еще раз.", buttons=[])

    def _handle_update_wizard(self, message: str) -> AssistantReply:
        assert self.wizard_state is not None
        draft = self.wizard_state["draft"]
        step = self.wizard_state["step"]
        normalized = message.strip().lower()

        if step == "field_choice":
            if normalized == "/update_title":
                self.wizard_state["step"] = "title_input"
                return self._reply_for_update_step()
            if normalized == "/update_date":
                self.wizard_state["step"] = "date_choice"
                return self._reply_for_update_step()
            if normalized == "/update_time":
                if not draft.get("due_date"):
                    self.wizard_state["step"] = "date_choice"
                    return self._reply_for_update_step(error_text="Сначала выбери дату, потом можно добавить время.")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_update_step()
            if normalized == "/update_priority":
                self.wizard_state["step"] = "priority"
                return self._reply_for_update_step()
            if normalized == "/apply_update":
                changes = self._build_update_changes_payload()
                if not self._has_update_changes(changes):
                    return self._reply_for_update_step(error_text="Пока ничего не изменилось. Выбери, что поправить.")
                self.wizard_state = None
                reply = self.dispatcher.dispatch(AgentCommand(action="update_task", data=changes))
                self._remember_pending_resolution(reply)
                return reply
            return self._reply_for_update_step(error_text="Выбери, что изменить в задаче.")

        if step == "title_input":
            inferred_category = self._infer_category(message.strip().lower())
            draft["category"] = inferred_category
            draft["title"] = self._infer_title(message.strip(), inferred_category)
            self.wizard_state["step"] = "field_choice"
            return self._reply_for_update_step()

        if step == "date_choice":
            if normalized in {"/clear_due_date", "без даты", "убрать дату"}:
                draft["due_date"] = ""
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_today", "сегодня"}:
                draft["due_date"] = self._parse_due_date_from_text("сегодня")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_tomorrow", "завтра"}:
                draft["due_date"] = self._parse_due_date_from_text("завтра")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_day_after_tomorrow", "послезавтра"}:
                draft["due_date"] = self._parse_due_date_from_text("послезавтра")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_next_week", "через неделю"}:
                draft["due_date"] = self._parse_due_date_from_text("через неделю")
                self.wizard_state["step"] = "time_choice"
                return self._reply_for_update_step()
            if self._parse_due_date_from_text(message) or self._extract_month_only(message):
                self.wizard_state["step"] = "date_input"
                return self._handle_update_wizard(message)
            self.wizard_state["step"] = "date_input"
            return self._reply_for_update_step()

        if step == "date_input":
            due_date = self._parse_due_date_from_text(message)
            if due_date:
                draft["due_date"] = due_date
                self.wizard_state["step"] = "field_choice" if self._text_has_explicit_time(message) else "time_choice"
                return self._reply_for_update_step()
            month_only = self._extract_month_only(message)
            if month_only:
                month_label = self._month_to_genitive(month_only)
                return self._make_wizard_reply(
                    answer=f"Понял месяц: {month_only}. Какое число поставить?",
                    buttons=[
                        {"label": f"1 {month_label}", "message": f"1 {month_label}"},
                        {"label": f"15 {month_label}", "message": f"15 {month_label}"},
                        {"label": f"30 {month_label}", "message": f"30 {month_label}"},
                        {"label": "Назад", "message": "/back_to_menu"},
                    ],
                    status={"mode": "Изменение задачи", "step": "Шаг 2: дата", "waiting": "Жду дату"},
                    draft=self._format_draft_preview(draft),
                )
            return self._reply_for_update_step(error_text="Не до конца понял дату. Напиши, например: завтра, 15 августа 2027 или через неделю.")

        if step == "time_choice":
            if normalized in {"/skip_time", "без времени", "оставить без времени"}:
                if draft.get("due_date"):
                    draft["due_date"] = self._normalize_due_without_time(draft["due_date"])
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_0900", "09:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("09:00"))
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_1200", "12:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("12:00"))
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_1800", "18:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("18:00"))
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            if normalized in {"/quick_2000", "20:00"}:
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], extract_time("20:00"))
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            self.wizard_state["step"] = "time_input"
            return self._reply_for_update_step()

        if step == "time_input":
            parsed_time = self._parse_time_from_text(message)
            if parsed_time is not None and draft.get("due_date"):
                draft["due_date"] = self._apply_time_to_due_date(draft["due_date"], parsed_time)
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            return self._reply_for_update_step(error_text="Не до конца понял время. Попробуй так: 18:00, 18-00 или 7 часов.")

        if step == "priority":
            priority = self._parse_priority_from_text(message)
            if priority is not None:
                draft["priority"] = priority
                self.wizard_state["step"] = "field_choice"
                return self._reply_for_update_step()
            return self._reply_for_update_step(error_text="Выбери приоритет: низкий, средний или высокий.")

        return self._reply_for_update_step()

    def _reply_for_create_step(self, error_text: str = "") -> AssistantReply:
        assert self.wizard_state is not None
        draft = self.wizard_state["draft"]
        step = self.wizard_state["step"]

        step_map = {
            "title": ("Создание задачи", "Шаг 1 из 5: название", "Жду название"),
            "date_choice": ("Создание задачи", "Шаг 2 из 5: дата", "Жду дату"),
            "date_input": ("Создание задачи", "Шаг 2 из 5: дата", "Жду дату"),
            "time_choice": ("Создание задачи", "Шаг 3 из 5: время", "Жду время"),
            "time_input": ("Создание задачи", "Шаг 3 из 5: время", "Жду время"),
            "priority": ("Создание задачи", "Шаг 4 из 5: приоритет", "Жду приоритет"),
            "confirm": ("Создание задачи", "Шаг 5 из 5: подтверждение", "Жду подтверждение"),
        }
        mode_label, step_label, waiting_label = step_map.get(step, ("Создание задачи", "", ""))

        answer_map = {
            "title": "Как назвать задачу?",
            "date_choice": f"Задача «{draft.get('title', 'Новая задача')}». Когда ее поставить?",
            "date_input": "Напиши дату в свободной форме. Например: завтра, послезавтра в 18:00 или через неделю.",
            "time_choice": "Добавить точное время или оставить без времени?",
            "time_input": "Напиши время в свободной форме. Например: 18:00, 18-00 или 7 часов.",
            "priority": "Выбери приоритет задачи.",
            "confirm": "Проверь черновик задачи и подтверди создание.",
        }

        buttons_map = {
            "title": [],
            "date_choice": [
                {"label": "Сегодня", "message": "/quick_today"},
                {"label": "Завтра", "message": "/quick_tomorrow"},
                {"label": "Послезавтра", "message": "/quick_day_after_tomorrow"},
                {"label": "Через неделю", "message": "/quick_next_week"},
                {"label": "Без даты", "message": "/skip_due_date"},
            ],
            "date_input": [],
            "time_choice": [
                {"label": "09:00", "message": "/quick_0900"},
                {"label": "12:00", "message": "/quick_1200"},
                {"label": "18:00", "message": "/quick_1800"},
                {"label": "20:00", "message": "/quick_2000"},
                {"label": "Без времени", "message": "/skip_time"},
            ],
            "time_input": [],
            "priority": [
                {"label": "Низкий", "message": "/priority_1"},
                {"label": "Средний", "message": "/priority_2"},
                {"label": "Высокий", "message": "/priority_3"},
            ],
            "confirm": [
                {"label": "Создать", "message": "/confirm_create"},
                {"label": "Название", "message": "/edit_title"},
                {"label": "Дата", "message": "/edit_date"},
                {"label": "Время", "message": "/edit_time"},
                {"label": "Приоритет", "message": "/edit_priority"},
            ],
        }

        answer = error_text or answer_map.get(step, "Продолжим.")
        return self._make_wizard_reply(
            answer=answer,
            buttons=buttons_map.get(step, []) + [{"label": "Назад", "message": "/back_to_menu"}],
            status={"mode": mode_label, "step": step_label, "waiting": waiting_label},
            draft=self._format_draft_preview(draft),
        )

    def _reply_for_update_step(self, error_text: str = "") -> AssistantReply:
        assert self.wizard_state is not None
        draft = self.wizard_state["draft"]
        step = self.wizard_state["step"]

        step_map = {
            "field_choice": ("Изменение задачи", "Шаг 1: выбор поля", "Жду действие"),
            "title_input": ("Изменение задачи", "Шаг 2: название", "Жду название"),
            "date_choice": ("Изменение задачи", "Шаг 2: дата", "Жду дату"),
            "date_input": ("Изменение задачи", "Шаг 2: дата", "Жду дату"),
            "time_choice": ("Изменение задачи", "Шаг 3: время", "Жду время"),
            "time_input": ("Изменение задачи", "Шаг 3: время", "Жду время"),
            "priority": ("Изменение задачи", "Шаг 4: приоритет", "Жду приоритет"),
        }
        mode_label, step_label, waiting_label = step_map.get(step, ("Изменение задачи", "", ""))

        answer_map = {
            "field_choice": f"Что изменить в задаче «{draft.get('title', 'Задача')}»?",
            "title_input": "Напиши новое название задачи.",
            "date_choice": "Выбери дату или оставь задачу без даты.",
            "date_input": "Напиши дату в свободной форме. Например: завтра, 15 августа 2027 или через неделю.",
            "time_choice": "Выбери время или оставь без времени.",
            "time_input": "Напиши время в свободной форме. Например: 18:00, 18-00 или 7 часов.",
            "priority": "Выбери новый приоритет задачи.",
        }

        buttons_map = {
            "field_choice": [
                {"label": "Название", "message": "/update_title"},
                {"label": "Дата", "message": "/update_date"},
                {"label": "Время", "message": "/update_time"},
                {"label": "Приоритет", "message": "/update_priority"},
                {"label": "Сохранить", "message": "/apply_update"},
            ],
            "title_input": [],
            "date_choice": [
                {"label": "Сегодня", "message": "/quick_today"},
                {"label": "Завтра", "message": "/quick_tomorrow"},
                {"label": "Послезавтра", "message": "/quick_day_after_tomorrow"},
                {"label": "Через неделю", "message": "/quick_next_week"},
                {"label": "Без даты", "message": "/clear_due_date"},
            ],
            "date_input": [],
            "time_choice": [
                {"label": "09:00", "message": "/quick_0900"},
                {"label": "12:00", "message": "/quick_1200"},
                {"label": "18:00", "message": "/quick_1800"},
                {"label": "20:00", "message": "/quick_2000"},
                {"label": "Без времени", "message": "/skip_time"},
            ],
            "time_input": [],
            "priority": [
                {"label": "Низкий", "message": "/priority_1"},
                {"label": "Средний", "message": "/priority_2"},
                {"label": "Высокий", "message": "/priority_3"},
            ],
        }

        answer = error_text or answer_map.get(step, "Продолжим изменение задачи.")
        return self._make_wizard_reply(
            answer=answer,
            buttons=buttons_map.get(step, []) + [{"label": "Назад", "message": "/back_to_menu"}],
            status={"mode": mode_label, "step": step_label, "waiting": waiting_label},
            draft=self._format_draft_preview(draft),
        )

    def _build_update_changes_payload(self) -> dict[str, Any]:
        assert self.wizard_state is not None
        draft = self.wizard_state["draft"]
        original = self.wizard_state["original"]
        payload: dict[str, Any] = {"task_id": self.wizard_state["task_id"]}

        for field in ("title", "description", "category", "recurrence", "priority"):
            if draft.get(field) != original.get(field):
                payload[field] = draft.get(field)

        if draft.get("due_date") != original.get("due_date"):
            if draft.get("due_date"):
                payload["due_date"] = draft["due_date"]
            else:
                payload["clear_due_date"] = True

        return payload

    def _make_wizard_reply(
        self,
        answer: str,
        buttons: list[dict[str, str]],
        status: Optional[dict[str, str]] = None,
        draft: Optional[dict[str, str]] = None,
    ) -> AssistantReply:
        reply = AssistantReply(action="clarify", data={}, answer=answer, should_refresh=False)
        reply.ui_hints = {"buttons": buttons, "status": status or {}, "draft": draft or {}}
        return reply


    def _next_create_reply(self, payload: dict[str, Any]) -> AssistantReply:
        if payload.get("due_date"):
            return self._build_time_choice_reply(payload)
        reply = AssistantReply(
            action="clarify",
            data={
                "pending_action": "create_task",
                "missing_field": "due_date_choice",
                "payload": payload,
            },
            answer=f"Задачу «{payload.get('title', 'Новая задача')}» записал. Поставить дату и время или оставить без даты?",
            should_refresh=False,
        )
        reply.ui_hints = self.dispatcher._build_ui_hints(reply)
        return reply

    def _build_time_choice_reply(self, payload: dict[str, Any]) -> AssistantReply:
        reply = AssistantReply(
            action="clarify",
            data={
                "pending_action": "create_task",
                "missing_field": "time_choice",
                "payload": payload,
            },
            answer="Добавить точное время или оставить без времени?",
            should_refresh=False,
        )
        reply.ui_hints = self.dispatcher._build_ui_hints(reply)
        return reply

    def _build_priority_reply(self, payload: dict[str, Any]) -> AssistantReply:
        reply = AssistantReply(
            action="clarify",
            data={
                "pending_action": "create_task",
                "missing_field": "priority",
                "payload": payload,
            },
            answer="Выбери приоритет задачи.",
            should_refresh=False,
        )
        reply.ui_hints = self.dispatcher._build_ui_hints(reply)
        return reply

    @staticmethod
    def _parse_priority_from_text(text: str) -> Optional[int]:
        normalized = text.lower().strip()
        if normalized in {"/priority_1", "низкий", "низкий приоритет"}:
            return 1
        if normalized in {"/priority_2", "средний", "средний приоритет"}:
            return 2
        if normalized in {"/priority_3", "высокий", "высокий приоритет"}:
            return 3
        return None

    @staticmethod
    def _parse_due_date_from_text(text: str) -> str:
        parsed = parse_relative_datetime(text.lower(), datetime.now())
        if parsed.due_at is not None:
            return parsed.due_at.strftime("%Y-%m-%d %H:%M")
        return ""

    @staticmethod
    def _task_to_candidate(task: Any) -> dict[str, Any]:
        return {
            "id": int(task.id),
            "title": str(task.title),
        }

    @staticmethod
    def _build_candidate_prompt(tasks: list[Any], title: str) -> str:
        lines = [title]
        for index, task in enumerate(tasks[:7], start=1):
            lines.append(f"{index}. {task.title}")
        return "\n".join(lines)

    @staticmethod
    def _task_to_wizard_draft(task: Any) -> dict[str, Any]:
        priority_map = {"низкий": 1, "средний": 2, "высокий": 3}
        due_date = ""
        if getattr(task, "due_date", ""):
            due_time = getattr(task, "due_time", "") or "23:59"
            due_date = f"{task.due_date} {due_time[:5]}"
        recurrence = getattr(task, "recurrence", None)
        if recurrence == "одноразовая":
            recurrence = None
        return {
            "title": str(getattr(task, "title", "")).strip(),
            "description": str(getattr(task, "description", "")).strip(),
            "category": str(getattr(task, "category", "другое")).strip().lower() or "другое",
            "due_date": due_date.strip(),
            "recurrence": recurrence,
            "priority": priority_map.get(str(getattr(task, "priority", "средний")).strip().lower(), 2),
        }

    @staticmethod
    def _extract_month_only(text: str) -> str:
        match = re.fullmatch(
            r"\s*(январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь)\s*",
            text.strip().lower(),
        )
        if not match:
            return ""
        return match.group(1)

    @staticmethod
    def _month_to_genitive(month_name: str) -> str:
        forms = {
            "январь": "января",
            "февраль": "февраля",
            "март": "марта",
            "апрель": "апреля",
            "май": "мая",
            "июнь": "июня",
            "июль": "июля",
            "август": "августа",
            "сентябрь": "сентября",
            "октябрь": "октября",
            "ноябрь": "ноября",
            "декабрь": "декабря",
        }
        return forms.get(month_name, month_name)

    @staticmethod
    def _parse_time_from_text(text: str):
        return extract_time(text.lower())

    @staticmethod
    def _text_has_explicit_time(text: str) -> bool:
        return extract_time(text.lower()) is not None

    @staticmethod
    def _apply_time_to_due_date(due_date: str, parsed_time) -> str:
        normalized = TaskAIAgent._normalize_due_date_string(due_date)
        base = datetime.strptime(normalized, "%Y-%m-%d %H:%M")
        updated = base.replace(hour=parsed_time.hour, minute=parsed_time.minute)
        return updated.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _normalize_due_without_time(due_date: str) -> str:
        normalized = TaskAIAgent._normalize_due_date_string(due_date)
        base = datetime.strptime(normalized, "%Y-%m-%d %H:%M")
        updated = base.replace(hour=23, minute=59)
        return updated.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _cleanup_title(value: str) -> str:
        cleaned = value.replace("ё", "е").strip()
        cleaned = TaskAIAgent._remove_obscene_words(cleaned)
        cleaned = re.sub(r"[^\w\s\-]", "", cleaned, flags=re.UNICODE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        stop_prefixes = (
            "сходить ",
            "сделать ",
            "надо ",
            "нужно ",
            "буду ",
            "поехать ",
            "поеду ",
        )
        for prefix in stop_prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                break
        if not cleaned:
            return "Новая задача"
        return TaskAIAgent._sentence_case(TaskAIAgent._normalize_named_phrase(cleaned))

    @staticmethod
    def _strip_task_noise(text: str) -> str:
        cleaned = text.lower()
        cleaned = re.sub(
            r"\b(добавь|добавить|запиши|записать|создай|создать|поставь|поставить|напомни|напомнить|мне|пожалуйста)\b",
            " ",
            cleaned,
        )
        cleaned = re.sub(
            r"\b(сегодня|завтра|послезавтра|через|неделю|месяц|дня|дней|понедельник|вторник|среду|среда|четверг|пятницу|пятница|субботу|суббота|воскресенье)\b",
            " ",
            cleaned,
        )
        cleaned = re.sub(r"\b\d{1,2}[:\-\.]\d{2}\b", " ", cleaned)
        cleaned = re.sub(r"\b\d[\d\s]*\s*руб(?:лей|ля|\.|)\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,!?:;\"'")
        return cleaned

    @staticmethod
    def _remove_obscene_words(text: str) -> str:
        bad_words = (
            "хер",
            "хрен",
            "блин",
            "блять",
            "нахер",
            "нахрен",
            "черт",
            "чёрт",
            "фиг",
        )
        cleaned = text
        for word in bad_words:
            cleaned = re.sub(rf"\b{re.escape(word)}\b", " ", cleaned, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _normalize_named_phrase(text: str) -> str:
        replacements = {
            "tv": "ТВ",
            "youtube": "YouTube",
            "okko": "OKKO",
            "ivi": "IVI",
            "spotify": "Spotify",
            "netflix": "Netflix",
            "москва": "Москва",
            "москву": "Москву",
            "питер": "Питер",
            "санкт-петербург": "Санкт-Петербург",
        }
        words: list[str] = []
        for raw_word in text.split():
            word = raw_word.strip(" .,!?:;\"'")
            if not word:
                continue
            normalized = replacements.get(word.lower())
            if normalized:
                words.append(normalized)
                continue
            if re.search(r"[a-zA-Z]", word):
                words.append(word[:1].upper() + word[1:].lower())
            else:
                words.append(word.lower())
        return " ".join(words).strip() or "Новая задача"

    @staticmethod
    def _sentence_case(text: str) -> str:
        if not text:
            return "Новая задача"
        return text[:1].upper() + text[1:]

    @staticmethod
    def _looks_like_cancel_command(message: str) -> bool:
        normalized = message.lower().strip()
        return normalized in {"/cancel", "отмена", "отменить", "начать заново", "/restart"}

    @staticmethod
    def _due_date_has_custom_time(due_date: str) -> bool:
        normalized = TaskAIAgent._normalize_due_date_string(due_date)
        return not normalized.endswith("23:59")

    @staticmethod
    def _format_draft_preview(draft: dict[str, Any]) -> dict[str, str]:
        priority_map = {1: "низкий", 2: "средний", 3: "высокий"}
        due_date = draft.get("due_date", "")
        due_label = "не выбрана"
        time_label = "не выбрано"
        if due_date:
            normalized = TaskAIAgent._normalize_due_date_string(due_date)
            parsed = datetime.strptime(normalized, "%Y-%m-%d %H:%M")
            due_label = parsed.strftime("%d.%m.%Y")
            time_label = "без времени" if parsed.strftime("%H:%M") == "23:59" else parsed.strftime("%H:%M")
        return {
            "Название": draft.get("title", "") or "не задано",
            "Категория": draft.get("category", "другое") or "другое",
            "Дата": due_label,
            "Время": time_label,
            "Приоритет": priority_map.get(int(draft.get("priority", 2)), "средний"),
        }
