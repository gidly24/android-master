from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_config import AISettings


def main() -> None:
    settings = AISettings.from_env()
    local_enabled = os.getenv("TASK_LOCAL_INTENT_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
    local_threshold = os.getenv("TASK_LOCAL_INTENT_MIN_CONFIDENCE", "0.55").strip() or "0.55"
    local_path_env = os.getenv("TASK_INTENT_MODEL_PATH", "").strip()
    local_model_path = Path(local_path_env) if local_path_env else ROOT / "models" / "intent_model.joblib"
    if not local_model_path.is_absolute():
        local_model_path = ROOT / local_model_path
    action_enabled = os.getenv("TASK_LOCAL_ACTION_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
    action_threshold = os.getenv("TASK_LOCAL_ACTION_MIN_CONFIDENCE", "0.55").strip() or "0.55"
    action_path_env = os.getenv("TASK_ACTION_MODEL_PATH", "").strip()
    action_model_path = Path(action_path_env) if action_path_env else ROOT / "models" / "action_router.joblib"
    if not action_model_path.is_absolute():
        action_model_path = ROOT / action_model_path
    print(f"provider={settings.provider}")
    print(f"base_url={settings.base_url}")
    print(f"model={settings.model}")
    print(f"configured={settings.is_configured}")
    print(f"local_action_enabled={action_enabled}")
    print(f"local_action_min_confidence={action_threshold}")
    print(f"local_action_model_path={action_model_path}")
    print(f"local_action_model_exists={action_model_path.exists()}")
    print(f"local_intent_enabled={local_enabled}")
    print(f"local_intent_min_confidence={local_threshold}")
    print(f"local_intent_model_path={local_model_path}")
    print(f"local_intent_model_exists={local_model_path.exists()}")


if __name__ == "__main__":
    main()
