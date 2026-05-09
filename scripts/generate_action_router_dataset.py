from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path


TRAIN_OUT = Path("data/action_router_train.jsonl")
VALIDATION_OUT = Path("data/action_router_validation.jsonl")
SPLIT_RATIO = 0.85

TITLES = [
    "купить молоко",
    "оплатить интернет",
    "позвонить маме",
    "записаться к врачу",
    "подготовить отчет",
    "сходить в аптеку",
    "помыть машину",
    "погасить кредит",
]

DATE_HINTS = [
    "сегодня",
    "завтра",
    "послезавтра",
    "через неделю",
]

TIME_HINTS = [
    "в 09:00",
    "в 12:30",
    "в 18:00",
    "в 20:15",
]


def _append_create(samples: list[dict[str, str]]) -> None:
    verbs = ["добавь", "создай", "запиши", "поставь задачу"]
    for title in TITLES:
        for verb in verbs:
            samples.append({"text": f"{verb} {title}", "action": "create_task"})
            for date_hint in DATE_HINTS:
                samples.append({"text": f"{verb} {date_hint} {title}", "action": "create_task"})
                for time_hint in TIME_HINTS:
                    samples.append({"text": f"{verb} {date_hint} {time_hint} {title}", "action": "create_task"})


def _append_delete(samples: list[dict[str, str]]) -> None:
    verbs = ["удали", "удалить", "убери"]
    for title in TITLES:
        for verb in verbs:
            samples.append({"text": f"{verb} {title}", "action": "delete_task"})
            samples.append({"text": f"{verb} задачу {title}", "action": "delete_task"})


def _append_done(samples: list[dict[str, str]]) -> None:
    templates = [
        "отметь {title} как выполненную",
        "выполнил {title}",
        "закрой {title}",
        "заверши {title}",
    ]
    for title in TITLES:
        for template in templates:
            samples.append({"text": template.format(title=title), "action": "mark_as_done"})


def _append_update(samples: list[dict[str, str]]) -> None:
    templates = [
        "перенеси {title} на завтра",
        "измени {title} на послезавтра",
        "обнови {title}, дедлайн через неделю",
        "поменяй срок у {title} на 15.08.2030",
        "перенеси {title} на 19.12.2030 в 09:00",
    ]
    for title in TITLES:
        for template in templates:
            samples.append({"text": template.format(title=title), "action": "update_task"})


def _append_list(samples: list[dict[str, str]]) -> None:
    phrases = [
        "покажи задачи",
        "список задач",
        "какие дела на завтра",
        "покажи просроченные задачи",
        "покажи активные задачи",
        "что у меня на этой неделе",
    ]
    for phrase in phrases:
        samples.append({"text": phrase, "action": "list_tasks"})


def _append_stats(samples: list[dict[str, str]]) -> None:
    phrases = [
        "покажи статистику",
        "сколько просроченных задач",
        "сколько всего задач",
        "какая статистика по задачам",
    ]
    for phrase in phrases:
        samples.append({"text": phrase, "action": "get_statistics"})


def _append_clarify(samples: list[dict[str, str]]) -> None:
    phrases = [
        "эээ",
        "не понял",
        "алло",
        "что-то",
        "ну и",
    ]
    for phrase in phrases:
        samples.append({"text": phrase, "action": "clarify"})


def _dedupe(samples: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for sample in samples:
        key = (sample["text"].strip().lower(), sample["action"].strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(sample)
    return unique


def _write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    samples: list[dict[str, str]] = []
    _append_create(samples)
    _append_delete(samples)
    _append_done(samples)
    _append_update(samples)
    _append_list(samples)
    _append_stats(samples)
    _append_clarify(samples)

    samples = _dedupe(samples)
    random.seed(42)
    random.shuffle(samples)

    split_at = int(len(samples) * SPLIT_RATIO)
    split_at = max(1, min(split_at, len(samples) - 1))
    train_rows = samples[:split_at]
    validation_rows = samples[split_at:]

    _write_jsonl(TRAIN_OUT, train_rows)
    _write_jsonl(VALIDATION_OUT, validation_rows)

    action_counts = Counter(item["action"] for item in samples)
    print(f"Total: {len(samples)}")
    print(f"Train: {len(train_rows)} -> {TRAIN_OUT}")
    print(f"Validation: {len(validation_rows)} -> {VALIDATION_OUT}")
    print("By action:")
    for action, count in sorted(action_counts.items()):
        print(f"  {action}: {count}")


if __name__ == "__main__":
    main()
