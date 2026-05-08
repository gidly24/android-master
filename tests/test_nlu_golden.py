from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nlu_adapter import parse_user_message


DATASET_PATH = Path("data/nlu_golden.jsonl")


def load_cases() -> list[dict]:
    if not DATASET_PATH.exists():
        return []
    cases: list[dict] = []
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    return value


@pytest.mark.parametrize("case", load_cases())
def test_nlu_golden(case: dict) -> None:
    text = case["text"]
    expected = case["expected"]
    actual = parse_user_message(text)

    assert actual["action"] == expected["action"], f"Wrong action for text: {text}"

    expected_data = expected.get("data", {})
    actual_data = actual.get("data", {})

    for key, expected_value in expected_data.items():
        assert key in actual_data, f"Missing field '{key}' for text: {text}"
        assert normalize(actual_data[key]) == normalize(expected_value), (
            f"Wrong field '{key}' for text: {text}. "
            f"Expected {expected_value}, got {actual_data.get(key)}"
        )
