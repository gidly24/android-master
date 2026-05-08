from __future__ import annotations

import json
import random
from pathlib import Path


INPUTS = [
    Path("data/nlu_golden.jsonl"),
    Path("data/nlu_synthetic.jsonl"),
]

TRAIN_OUT = Path("data/nlu_train.jsonl")
VAL_OUT = Path("data/nlu_validation.jsonl")
SPLIT_RATIO = 0.8


def load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    if not path.exists():
        return items
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def dedupe(items: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen: set[str] = set()
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for item in items:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")


def main() -> None:
    all_items: list[dict] = []
    for path in INPUTS:
        all_items.extend(load_jsonl(path))

    all_items = dedupe(all_items)
    random.seed(42)
    random.shuffle(all_items)

    if not all_items:
        write_jsonl(TRAIN_OUT, [])
        write_jsonl(VAL_OUT, [])
        print("No input items found. Created empty train/validation files.")
        return

    split_index = int(len(all_items) * SPLIT_RATIO)
    split_index = max(1, min(split_index, len(all_items) - 1))

    train_items = all_items[:split_index]
    val_items = all_items[split_index:]

    write_jsonl(TRAIN_OUT, train_items)
    write_jsonl(VAL_OUT, val_items)

    print(f"Total: {len(all_items)}")
    print(f"Train: {len(train_items)} -> {TRAIN_OUT}")
    print(f"Validation: {len(val_items)} -> {VAL_OUT}")


if __name__ == "__main__":
    main()
