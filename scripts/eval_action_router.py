import argparse
import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.metrics import accuracy_score, classification_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate local action router model.")
    parser.add_argument("--model", default="models/action_router.joblib", help="Model path.")
    parser.add_argument("--test", default="data/action_router_validation.jsonl", help="Test JSONL path.")
    parser.add_argument("--report-out", default="reports/action_router_eval.txt", help="Evaluation report path.")
    parser.add_argument(
        "--errors-out",
        default="reports/action_router_errors.jsonl",
        help="Misclassified samples path.",
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
        action = str(row.get("action", "")).strip()
        if not text or not action:
            continue
        x.append(text)
        y.append(action)
    if not x:
        raise RuntimeError("Dataset is empty after filtering.")
    return x, y


def main() -> None:
    args = parse_args()
    model_path = Path(args.model).resolve()
    rows = read_jsonl(Path(args.test).resolve())
    x_test, y_test = to_xy(rows)

    bundle = joblib.load(model_path)
    model = bundle["pipeline"] if isinstance(bundle, dict) and "pipeline" in bundle else bundle
    predictions = model.predict(x_test)

    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, digits=4, zero_division=0)

    report_path = Path(args.report_out).resolve()
    errors_path = Path(args.errors_out).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    errors_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"Accuracy: {accuracy:.4f}\n\n")
        handle.write(report)

    with errors_path.open("w", encoding="utf-8") as handle:
        for text, expected, predicted in zip(x_test, y_test, predictions):
            if expected == predicted:
                continue
            handle.write(
                json.dumps(
                    {"text": text, "expected_action": expected, "predicted_action": str(predicted)},
                    ensure_ascii=False,
                )
                + "\n"
            )

    print("Evaluation completed.")
    print(f"Samples: {len(x_test)}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Report: {report_path}")
    print(f"Errors: {errors_path}")


if __name__ == "__main__":
    main()
