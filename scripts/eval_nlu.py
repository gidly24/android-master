from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nlu_adapter import parse_user_message


DATASET_PATH = Path("data/nlu_validation.jsonl")
ERRORS_OUT = Path("reports/nlu_errors.jsonl")


def load_jsonl(path: Path) -> list[dict]:
    cases: list[dict] = []
    if not path.exists():
        return cases
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def compare_case(case: dict) -> dict:
    text = case["text"]
    expected = case["expected"]
    actual = parse_user_message(text)

    result = {
        "text": text,
        "expected": expected,
        "actual": actual,
        "action_ok": False,
        "slots_total": 0,
        "slots_ok": 0,
        "errors": [],
    }

    if actual.get("action") == expected.get("action"):
        result["action_ok"] = True
    else:
        result["errors"].append(
            {
                "type": "wrong_action",
                "expected": expected.get("action"),
                "actual": actual.get("action"),
            }
        )

    expected_data = expected.get("data", {})
    actual_data = actual.get("data", {})

    for key, expected_value in expected_data.items():
        result["slots_total"] += 1
        actual_value = actual_data.get(key)
        if normalize(actual_value) == normalize(expected_value):
            result["slots_ok"] += 1
        else:
            result["errors"].append(
                {
                    "type": "wrong_slot",
                    "field": key,
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )

    result["ok"] = result["action_ok"] and result["slots_ok"] == result["slots_total"]
    return result


def main() -> None:
    cases = load_jsonl(DATASET_PATH)
    if not cases:
        print(f"No validation cases found at {DATASET_PATH}")
        return

    total = len(cases)
    action_ok = 0
    slots_ok = 0
    slots_total = 0
    full_ok = 0
    errors: list[dict] = []
    clarify_count = 0
    false_clarify_count = 0

    for case in cases:
        result = compare_case(case)
        expected_action = case.get("expected", {}).get("action")
        actual_action = result.get("actual", {}).get("action")

        if actual_action == "clarify":
            clarify_count += 1
            if expected_action != "clarify":
                false_clarify_count += 1

        if result["action_ok"]:
            action_ok += 1

        slots_ok += result["slots_ok"]
        slots_total += result["slots_total"]

        if result["ok"]:
            full_ok += 1
        else:
            errors.append(result)

    ERRORS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with ERRORS_OUT.open("w", encoding="utf-8") as file:
        for item in errors:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("NLU validation report")
    print("---------------------")
    print(f"Total cases:      {total}")
    print(f"Full accuracy:    {full_ok / total:.2%}")
    print(f"Action accuracy:  {action_ok / total:.2%}")
    if slots_total:
        print(f"Slot accuracy:    {slots_ok / slots_total:.2%}")
    else:
        print("Slot accuracy:    n/a (no expected slots)")
    print(f"Clarify rate:     {clarify_count / total:.2%}")
    print(f"False clarify:    {false_clarify_count / total:.2%}")
    print(f"Errors:           {len(errors)}")
    print(f"Errors file:      {ERRORS_OUT}")


if __name__ == "__main__":
    main()
