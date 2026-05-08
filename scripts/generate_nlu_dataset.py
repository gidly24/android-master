from __future__ import annotations

import json
import random
from pathlib import Path


OUT_PATH = Path("data/nlu_synthetic.jsonl")

TITLES = [
    "купить хлеб",
    "купить корм",
    "позвонить маме",
    "позвонить клиенту",
    "сделать отчет",
    "оплатить интернет",
    "записаться к врачу",
    "забрать заказ",
    "убрать дома",
    "подготовить презентацию",
]

DATE_PHRASES = [
    "сегодня",
    "завтра",
    "послезавтра",
    "через неделю",
]

TIME_PHRASES = [
    "в 09:00",
    "в 12:30",
    "в 18:00",
    "в 20:15",
]

PRIORITY_PHRASES = [
    ("важно", 3),
    ("срочно", 3),
    ("обычный приоритет", 2),
    ("низкий приоритет", 1),
]

LIST_PHRASES = [
    ("покажи все задачи", {}),
    ("покажи активные задачи", {"view": "actual"}),
    ("покажи просроченные задачи", {"status": "просрочена"}),
    ("покажи задачи на этой неделе", {}),
]

CLARIFY_PHRASES = [
    "эээ",
    "ну и?",
    "не понял",
    "что-то",
]


def _append_create(examples: list[dict]) -> None:
    for title in TITLES:
        for date_phrase in DATE_PHRASES:
            examples.append(
                {
                    "text": f"добавь {date_phrase} {title}",
                    "expected": {"action": "create_task", "data": {}},
                }
            )

            for time_phrase in TIME_PHRASES:
                examples.append(
                    {
                        "text": f"добавь {date_phrase} {time_phrase} {title}",
                        "expected": {"action": "create_task", "data": {}},
                    }
                )

            for priority_text, priority_value in PRIORITY_PHRASES:
                examples.append(
                    {
                        "text": f"добавь {date_phrase} {title}, {priority_text}",
                        "expected": {"action": "create_task", "data": {"priority": priority_value}},
                    }
                )

        examples.append(
            {
                "text": f"добавь {title}",
                "expected": {"action": "clarify", "data": {"missing_field": "due_date_choice"}},
            }
        )


def _append_delete(examples: list[dict]) -> None:
    for title in TITLES:
        examples.append(
            {
                "text": f"удали {title}",
                "expected": {"action": "delete_task", "data": {"title_query": title}},
            }
        )


def _append_mark_done(examples: list[dict]) -> None:
    for title in TITLES:
        examples.append(
            {
                "text": f"отметь {title} как выполненную",
                "expected": {"action": "mark_as_done", "data": {"title_query": title}},
            }
        )


def _append_update(examples: list[dict]) -> None:
    absolute_dates = ["15.08.2030", "16.09.2030", "17.10.2030", "18.11.2030"]
    absolute_date_times = [
        "19.12.2030 в 09:00",
        "20.12.2030 в 12:30",
        "21.12.2030 в 18:00",
        "22.12.2030 в 20:15",
    ]
    for idx, title in enumerate(TITLES):
        date_phrase = absolute_dates[idx % len(absolute_dates)]
        examples.append(
            {
                "text": f"перенеси {title} на {date_phrase}",
                "expected": {"action": "update_task", "data": {"title_query": title}},
            }
        )
        date_time_phrase = absolute_date_times[idx % len(absolute_date_times)]
        examples.append(
            {
                "text": f"перенеси {title} на {date_time_phrase}",
                "expected": {"action": "update_task", "data": {"title_query": title}},
            }
        )


def _append_list_and_stats(examples: list[dict]) -> None:
    for text, data in LIST_PHRASES:
        examples.append({"text": text, "expected": {"action": "list_tasks", "data": data}})

    examples.extend(
        [
            {"text": "сколько у меня просроченных дел", "expected": {"action": "get_statistics", "data": {}}},
            {"text": "покажи статистику по задачам", "expected": {"action": "get_statistics", "data": {}}},
        ]
    )


def _append_clarify(examples: list[dict]) -> None:
    for text in CLARIFY_PHRASES:
        examples.append({"text": text, "expected": {"action": "clarify", "data": {}}})


def _deduplicate(examples: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict] = []
    for example in examples:
        text = example["text"].strip()
        action = example["expected"]["action"]
        data_key = json.dumps(example["expected"].get("data", {}), ensure_ascii=False, sort_keys=True)
        key = (text, action, data_key)
        if key in seen:
            continue
        seen.add(key)
        unique.append(example)
    return unique


def main() -> None:
    examples: list[dict] = []
    _append_create(examples)
    _append_delete(examples)
    _append_mark_done(examples)
    _append_update(examples)
    _append_list_and_stats(examples)
    _append_clarify(examples)

    examples = _deduplicate(examples)
    random.seed(42)
    random.shuffle(examples)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as file:
        for item in examples:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Generated {len(examples)} examples -> {OUT_PATH}")


if __name__ == "__main__":
    main()
