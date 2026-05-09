import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datasets import load_dataset

DATASET_NAME = "AmazonScience/massive"
DEFAULT_CONFIG = "ru-RU"
DEFAULT_SPLITS = ("train", "validation", "test")
TEXT_COLUMNS = ("utt", "utterance", "text", "annot_utt")
INTENT_COLUMNS = ("intent", "intent_num")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download MASSIVE and export ru-RU intent data to JSONL."
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Dataset configuration.")
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory where JSONL files will be written.",
    )
    parser.add_argument(
        "--max-per-split",
        type=int,
        default=0,
        help="Limit examples per split (0 means all).",
    )
    return parser.parse_args()


def _pick_column(available: list[str], candidates: tuple[str, ...], label: str) -> str:
    for candidate in candidates:
        if candidate in available:
            return candidate
    raise RuntimeError(f"Cannot find {label} column. Available: {available}")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(DATASET_NAME, args.config, trust_remote_code=True)
    train_split = dataset["train"]

    text_col = _pick_column(train_split.column_names, TEXT_COLUMNS, "text")
    intent_col = _pick_column(train_split.column_names, INTENT_COLUMNS, "intent")

    intent_feature = train_split.features[intent_col]
    intent_names = list(getattr(intent_feature, "names", []))

    summary: dict[str, Any] = {
        "dataset": DATASET_NAME,
        "config": args.config,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "text_column": text_col,
        "intent_column": intent_col,
        "intent_count": len(intent_names),
        "splits": {},
    }

    for split in DEFAULT_SPLITS:
        if split not in dataset:
            continue
        rows: list[dict[str, Any]] = []
        for sample in dataset[split]:
            text = str(sample.get(text_col, "")).strip()
            if not text:
                continue
            raw_intent = sample.get(intent_col)
            if raw_intent is None:
                continue

            try:
                intent_id = int(raw_intent)
            except (TypeError, ValueError):
                continue

            intent_name = (
                intent_names[intent_id]
                if 0 <= intent_id < len(intent_names)
                else str(raw_intent)
            )
            rows.append(
                {
                    "text": text,
                    "intent_id": intent_id,
                    "intent": intent_name,
                }
            )

        if args.max_per_split > 0:
            rows = rows[: args.max_per_split]

        target = output_dir / f"nlu_{split}.jsonl"
        _write_jsonl(target, rows)
        summary["splits"][split] = {"rows": len(rows), "file": target.name}

    if intent_names:
        summary["intent_labels"] = intent_names

    _write_jsonl(output_dir / "nlu_metadata.jsonl", [summary])

    print("Done.")
    print(f"Dataset: {DATASET_NAME} / {args.config}")
    print(f"Text column: {text_col}")
    print(f"Intent column: {intent_col}")
    for split, payload in summary["splits"].items():
        print(f"{split}: {payload['rows']} rows -> {payload['file']}")


if __name__ == "__main__":
    main()
