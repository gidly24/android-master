import argparse
import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.metrics import accuracy_score, classification_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a trained intent model on test JSONL data."
    )
    parser.add_argument("--model", default="models/intent_model.joblib", help="Model file path.")
    parser.add_argument("--test", default="data/nlu_test.jsonl", help="Test JSONL path.")
    parser.add_argument(
        "--report-out",
        default="reports/eval_report.txt",
        help="Path for full metrics report.",
    )
    parser.add_argument(
        "--errors-out",
        default="reports/eval_errors.jsonl",
        help="Path for misclassified examples.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def to_xy(rows: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    x: list[str] = []
    y: list[str] = []
    for row in rows:
        text = str(row.get("text", "")).strip()
        label = str(row.get("intent", "")).strip()
        if not text or not label:
            continue
        x.append(text)
        y.append(label)
    if not x:
        raise RuntimeError("Dataset is empty after filtering.")
    return x, y


def main() -> None:
    args = parse_args()
    model_path = Path(args.model).resolve()
    test_path = Path(args.test).resolve()
    report_path = Path(args.report_out).resolve()
    errors_path = Path(args.errors_out).resolve()

    bundle = joblib.load(model_path)
    model = bundle["pipeline"] if isinstance(bundle, dict) and "pipeline" in bundle else bundle

    test_rows = read_jsonl(test_path)
    x_test, y_test = to_xy(test_rows)
    predictions = model.predict(x_test)

    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, digits=4, zero_division=0)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    errors_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"Accuracy: {accuracy:.4f}\n\n")
        handle.write(report)

    error_rows: list[dict[str, str]] = []
    for text, expected, predicted in zip(x_test, y_test, predictions):
        if expected != predicted:
            error_rows.append(
                {
                    "text": text,
                    "expected_intent": expected,
                    "predicted_intent": str(predicted),
                }
            )

    with errors_path.open("w", encoding="utf-8") as handle:
        for row in error_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("Evaluation completed.")
    print(f"Test samples: {len(x_test)}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Report: {report_path}")
    print(f"Errors: {errors_path} ({len(error_rows)} rows)")


if __name__ == "__main__":
    main()
