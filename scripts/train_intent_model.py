import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a lightweight intent classifier on JSONL data."
    )
    parser.add_argument("--train", default="data/nlu_train.jsonl", help="Train JSONL path.")
    parser.add_argument(
        "--validation",
        default="data/nlu_validation.jsonl",
        help="Validation JSONL path.",
    )
    parser.add_argument(
        "--model-out",
        default="models/intent_model.joblib",
        help="Output model file.",
    )
    parser.add_argument(
        "--report-out",
        default="reports/train_report.txt",
        help="Path for training report.",
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
    train_path = Path(args.train).resolve()
    validation_path = Path(args.validation).resolve()
    model_path = Path(args.model_out).resolve()
    report_path = Path(args.report_out).resolve()

    train_rows = read_jsonl(train_path)
    validation_rows = read_jsonl(validation_path)
    x_train, y_train = to_xy(train_rows)
    x_validation, y_validation = to_xy(validation_rows)

    model = Pipeline(
        steps=[
            (
                "vectorizer",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    lowercase=True,
                    min_df=2,
                ),
            ),
            (
                "classifier",
                SGDClassifier(
                    loss="log_loss",
                    alpha=1e-5,
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(x_train, y_train)
    predictions = model.predict(x_validation)

    accuracy = accuracy_score(y_validation, predictions)
    report = classification_report(y_validation, predictions, digits=4, zero_division=0)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "train_samples": len(x_train),
        "validation_samples": len(x_validation),
        "accuracy": accuracy,
    }
    joblib.dump({"pipeline": model, "meta": payload}, model_path)

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"Accuracy: {accuracy:.4f}\n\n")
        handle.write(report)

    print("Training completed.")
    print(f"Train samples: {len(x_train)}")
    print(f"Validation samples: {len(x_validation)}")
    print(f"Validation accuracy: {accuracy:.4f}")
    print(f"Model: {model_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
