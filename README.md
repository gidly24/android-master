# Task Control — полный технический паспорт проекта

> Актуально на: **10 мая 2026**  
> Документ собран по фактическому состоянию каталога `C:\Users\iVN\PycharmProjects\PythonProject`.

## 1) Что это за проект

`Task Control` — локальное приложение на Python/Kivy для управления задачами с двумя способами работы:

1. классический UI (создать/изменить/выполнить/удалить/фильтровать/архив);
2. AI-чат на русском языке (NLP + роутинг действий + опциональный внешний LLM).

Проект работает локально, серверной части нет, основная БД — `SQLite`.

---

## 2) Платформы, фреймворки и ключевые библиотеки

### Runtime

- Python 3.11+ (в текущем окружении используется Python 3.12)
- [Kivy 2.3.1](https://kivy.org/doc/stable/)
- [sqlite3 (стандартная библиотека Python)](https://docs.python.org/3/library/sqlite3.html)
- [Pillow](https://pillow.readthedocs.io/en/stable/) (иконки/изображения, зависимость UI/сборки)

### AI/NLU/ML

- [scikit-learn](https://scikit-learn.org/stable/) — обучение локальных классификаторов
- [joblib](https://joblib.readthedocs.io/) — сериализация моделей
- [Hugging Face Datasets](https://huggingface.co/docs/datasets) — загрузка датасета
- Датасет: [AmazonScience/massive](https://huggingface.co/datasets/AmazonScience/massive), конфиг `ru-RU`

### Внешние AI API

- OpenAI-compatible `POST /chat/completions`:
  - [OpenAI API reference](https://platform.openai.com/docs/api-reference/chat/create)
  - DeepSeek через совместимый интерфейс

### Мобильная упаковка

- [Buildozer](https://buildozer.readthedocs.io/en/stable/specifications.html), Android-конфиг в `buildozer.spec`

---

## 3) Архитектура, иерархия и зависимости

## 3.1 Слои

1. **UI слой (`ui/*`, `main.py`)**
   - экраны задач и архива;
   - форма создания/редактирования;
   - чат-модалка для AI-диалога;
   - Android-native date/time picker через `pyjnius`.

2. **Бизнес-логика (`services.py`)**
   - валидация задачи;
   - статусы/просрочка/повторяемость;
   - сценарии CRUD из UI;
   - сценарии CRUD/list/stats из AI.

3. **Доступ к данным (`database.py`)**
   - CRUD в SQLite;
   - SQL-агрегации статистики;
   - SQL-обновление просрочки;
   - миграции/индексы.

4. **AI/NLU (`ai_agent.py`, `ai_date_parser.py`, `ai_config.py`)**
   - локальный action-router (`models/action_router.joblib`);
   - локальный intent classifier (`models/intent_model.joblib`);
   - fallback на внешний LLM;
   - fallback на эвристики;
   - мастера-уточнения (wizard) и candidate-resolution.

5. **ML pipeline scripts (`scripts/*`)**
   - подготовка данных MASSIVE;
   - генерация датасета для action-router;
   - train/eval для двух локальных моделей.

## 3.2 Импорт-зависимости между модулями

- `main.py` -> `database.py`, `services.py`, `ai_agent.py`, `ui/*`
- `services.py` -> `models.py`
- `database.py` -> `models.py`
- `ai_agent.py` -> `ai_config.py`, `ai_date_parser.py` (+ использует `TaskService` через dispatcher)
- `ui/screens.py` -> `services.py`, `models.py`, `ui/forms.py`, `ui/components.py`
- `ui/forms.py` -> `models.py`, `ui/android_pickers.py`, `ui/components.py`
- `ui/chat_screen.py` -> `ui/components.py`, агент передается извне (`TaskAIAgent`)
- `scripts/*` независимы от UI, работают как CLI

## 3.3 Поток взаимодействия (UI)

`TaskListScreen / ArchiveScreen` -> `TaskService` -> `DatabaseManager` -> `tasks.db`

## 3.4 Поток взаимодействия (AI)

`ChatModal.send_message()` -> `TaskAIAgent.process_message()` ->  
`(local action model -> local intent model -> LLM -> heuristic)` ->  
`TaskCommandDispatcher.dispatch()` -> `TaskService` -> `DatabaseManager`

---

## 4) Полная структура проекта (каждый файл)

Ниже перечислены **все файлы проекта вне `.venv`, `.git`, `__pycache__`**.

```text
PythonProject/
├─ .gitignore
├─ README.md
├─ ai_agent.py
├─ ai_config.py
├─ ai_date_parser.py
├─ buildozer.spec
├─ database.py
├─ guaranteed_phrases_ru.txt
├─ main.py
├─ models.py
├─ requirements-nlu.txt
├─ requirements.txt
├─ services.py
├─ tasks.db
├─ .idea/
│  ├─ PythonProject.iml
│  ├─ vcs.xml
│  ├─ workspace.xml
│  └─ inspectionProfiles/
│     ├─ Project_Default.xml
│     └─ profiles_settings.xml
├─ assets/
│  ├─ fonts/
│  │  └─ Roboto-Bold.ttf
│  └─ icons/
│     ├─ delete.ico
│     ├─ done.ico
│     ├─ edit.ico
│     └─ more.ico
├─ data/
│  ├─ action_router_train.jsonl
│  ├─ action_router_validation.jsonl
│  ├─ nlu_metadata.jsonl
│  ├─ nlu_test.jsonl
│  ├─ nlu_train.jsonl
│  └─ nlu_validation.jsonl
├─ models/
│  ├─ action_router.joblib
│  └─ intent_model.joblib
├─ reports/
│  ├─ action_router_errors.jsonl
│  ├─ action_router_eval.txt
│  ├─ action_router_report.txt
│  ├─ eval_errors.jsonl
│  ├─ eval_report.txt
│  └─ train_report.txt
├─ scripts/
│  ├─ eval_action_router.py
│  ├─ eval_intent_model.py
│  ├─ generate_action_router_dataset.py
│  ├─ prepare_massive_ru.py
│  ├─ show_active_llm.py
│  ├─ train_action_router.py
│  └─ train_intent_model.py
└─ ui/
   ├─ __init__.py
   ├─ android_pickers.py
   ├─ chat_screen.py
   ├─ components.py
   ├─ forms.py
   └─ screens.py
```

Примечание: в `.venv` сейчас >11k файлов зависимостей Python; это окружение, а не исходный код приложения.

---

## 5) Подробно по каждому файлу

### Корень проекта

- `.gitignore` — правила игнорирования (включая `tasks.db`, `data/*.jsonl`, `models/`, `reports/`, `.venv/`).
- `README.md` — этот документ.
- `main.py` — точка входа Kivy-приложения, wiring UI+Service+DB+AI.
- `models.py` — dataclass `Task` + доменные константы категорий/приоритетов/статусов.
- `database.py` — SQLite-слой (схема, индексы, CRUD, выборки, статистика).
- `services.py` — бизнес-слой задач, включая AI-friendly методы.
- `ai_config.py` — конфигурация внешнего LLM через env.
- `ai_date_parser.py` — парсер русских дат/времени (относительные/абсолютные).
- `ai_agent.py` — AI-оркестратор: local models + LLM + heuristics + wizard.
- `requirements.txt` — runtime-зависимости UI приложения.
- `requirements-nlu.txt` — зависимости для подготовки/обучения NLU-моделей.
- `buildozer.spec` — Android-сборка.
- `guaranteed_phrases_ru.txt` — словарь гарантированных фраз (локальный справочный файл; в коде не импортируется).
- `tasks.db` — локальная SQLite БД.

### `.idea/`

- `PythonProject.iml`, `vcs.xml`, `workspace.xml`, `inspectionProfiles/*` — служебные файлы IDE.

### `assets/`

- `fonts/Roboto-Bold.ttf` — шрифт UI.
- `icons/*.ico` — иконки action-кнопок задач.

### `ui/`

- `__init__.py` — маркер пакета.
- `components.py` — дизайн-система компонентов (кнопки, карточки, спиннеры, чипы, текстовые поля).
- `screens.py` — экраны списка задач и архива.
- `forms.py` — popup-форма создания/редактирования.
- `chat_screen.py` — AI-чат popup с быстрыми кнопками/драфтом/статусом.
- `android_pickers.py` — native Android date/time picker wrappers.

### `scripts/`

- `prepare_massive_ru.py` — загрузка `AmazonScience/massive` (`ru-RU`) и экспорт JSONL.
- `train_intent_model.py` — обучение `intent_model.joblib`.
- `eval_intent_model.py` — оценка intent модели на test split.
- `generate_action_router_dataset.py` — генерация синтетического датасета действий.
- `train_action_router.py` — обучение `action_router.joblib`.
- `eval_action_router.py` — оценка action-router модели.
- `show_active_llm.py` — печать активной AI-конфигурации и статуса локальных моделей.

### `data/` (локальные данные)

- `nlu_train.jsonl`, `nlu_validation.jsonl`, `nlu_test.jsonl` — intent выборки.
- `nlu_metadata.jsonl` — метаданные подготовки датасета.
- `action_router_train.jsonl`, `action_router_validation.jsonl` — action-router выборки.

### `models/` (локальные артефакты моделей)

- `intent_model.joblib` — локальный intent-классификатор.
- `action_router.joblib` — локальный роутер команд.

### `reports/` (локальные отчеты)

- `train_report.txt`, `eval_report.txt`, `eval_errors.jsonl` — отчеты intent модели.
- `action_router_report.txt`, `action_router_eval.txt`, `action_router_errors.jsonl` — отчеты action-router.

---

## 6) База данных

### 6.1 Тип БД

- **SQLite**, файл: `tasks.db`

### 6.2 Таблицы

1. `tasks`
   - `id` INTEGER PK AUTOINCREMENT
   - `title` TEXT NOT NULL
   - `description` TEXT
   - `category` TEXT NOT NULL
   - `due_date` TEXT NOT NULL
   - `due_time` TEXT NOT NULL DEFAULT `'23:59'`
   - `recurrence` TEXT NOT NULL
   - `priority` TEXT NOT NULL
   - `status` TEXT NOT NULL
   - `is_archived` INTEGER NOT NULL DEFAULT `0`
   - `archived_at` TEXT
   - `created_at` TEXT DEFAULT CURRENT_TIMESTAMP
   - `updated_at` TEXT DEFAULT CURRENT_TIMESTAMP

2. `app_state`
   - `key` TEXT PRIMARY KEY
   - `value` TEXT NOT NULL

### 6.3 Индексы

- `idx_tasks_active` on `(is_archived, status, due_date)`
- `idx_tasks_archived` on `(is_archived, archived_at)`

### 6.4 Логика статусов

- просрочка пересчитывается SQL-запросом `update_overdue_statuses`;
- одноразовая задача при завершении уходит в архив (`is_archived=1`);
- повторяющиеся задачи получают новую дату и остаются активными.

---

## 7) Как устроен AI

## 7.1 Компоненты

- `TaskAIAgent` (оркестратор)
- `TaskCommandDispatcher` (выполнение доменных действий через `TaskService`)
- `OpenAIClient` (внешний LLM клиент, OpenAI-compatible)
- `ai_date_parser` (локальный парсинг дат/времени на русском)
- локальные модели:
  - `models/action_router.joblib`
  - `models/intent_model.joblib`

## 7.2 Порядок обработки сообщения

1. Local action model (`action_router`)  
2. Local intent model (`intent_model`)  
3. Внешний LLM (`/chat/completions`)  
4. Эвристический fallback (`_heuristic_command`)  
5. Wizard/pending-resolution при неполных данных

## 7.3 Поддерживаемые действия

- `create_task`
- `delete_task`
- `mark_as_done`
- `update_task`
- `list_tasks`
- `get_statistics`
- `clarify`
- `back_to_menu`

## 7.4 Обучена ли AI-часть

### Что обучено в этом проекте

1. **Intent model (`intent_model.joblib`)**
   - обучена на `AmazonScience/massive`, конфиг `ru-RU`;
   - train/val/test из `data/nlu_*.jsonl`;
   - train samples: `11514`
   - validation samples: `2033`
   - accuracy (train script report): `0.8401`
   - eval на test (`reports/eval_report.txt`): `0.8352`

2. **Action router (`action_router.joblib`)**
   - обучен на синтетическом датасете из `scripts/generate_action_router_dataset.py`;
   - train samples: `685`
   - validation samples: `122`
   - accuracy: `0.9836`

### Что НЕ обучается в этом проекте

- Внешняя LLM (`OpenAI`/`DeepSeek`/`Claude`/`Gemini`, включая `ProxyAPI`) **не обучается локально** в этом репозитории.  
  Проект только отправляет запросы к API.

## 7.5 Переменные окружения AI

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `PROXYAPI_API_KEY`
- `TASK_AI_PROVIDER` (`openai` / `deepseek` / `proxyapi_openai` / `proxyapi_anthropic` / `proxyapi_gemini` / `proxyapi_compatible`)
- `TASK_AI_BASE_URL`
- `TASK_AI_API_KEY`
- `TASK_AI_MODEL`
- `TASK_AI_TIMEOUT`
- `TASK_LOCAL_ACTION_ENABLED`
- `TASK_LOCAL_ACTION_MIN_CONFIDENCE`
- `TASK_ACTION_MODEL_PATH`
- `TASK_LOCAL_INTENT_ENABLED`
- `TASK_LOCAL_INTENT_MIN_CONFIDENCE`
- `TASK_INTENT_MODEL_PATH`

---

## 8) Способы взаимодействия с системой

1. **GUI (desktop/mobile)**  
   - список задач, фильтры, поиск, карточки задач, архив.

2. **AI-чат**  
   - свободный русский текст + быстрые кнопки + уточняющие шаги wizard.

3. **CLI-скрипты обучения/оценки**  
   - подготовка данных, обучение, валидация, отчеты.

4. **Android-native pickers**  
   - выбор даты/времени через системные диалоги Android.

---

## 9) Скрипты: что делают и где результат

### 9.1 Подготовка данных

```bash
python scripts/prepare_massive_ru.py --config ru-RU
```

Выход: `data/nlu_train.jsonl`, `data/nlu_validation.jsonl`, `data/nlu_test.jsonl`, `data/nlu_metadata.jsonl`.

### 9.2 Обучение/оценка intent модели

```bash
python scripts/train_intent_model.py
python scripts/eval_intent_model.py
```

Выход: `models/intent_model.joblib`, `reports/train_report.txt`, `reports/eval_report.txt`, `reports/eval_errors.jsonl`.

### 9.3 Обучение/оценка action-router

```bash
python scripts/generate_action_router_dataset.py
python scripts/train_action_router.py
python scripts/eval_action_router.py
```

Выход: `data/action_router_train.jsonl`, `data/action_router_validation.jsonl`, `models/action_router.joblib`, `reports/action_router_report.txt`, `reports/action_router_eval.txt`, `reports/action_router_errors.jsonl`.

### 9.4 Диагностика активной AI-конфигурации

```bash
python scripts/show_active_llm.py
```

Печатает provider/base_url/model + флаги/пути локальных моделей.

---

## 10) Полный индекс классов, функций и методов (по исходникам)

> Ниже полный индекс кода для `*.py` (без `.venv` и `__pycache__`).

### `main.py`

- `TaskControlApp`: `build`, `on_start`, `_build_navigation`, `_build_screens`, `refresh_all_screens`, `clear_archive`, `switch_screen`, `open_chat_modal`, `_update_navigation`, `_force_layout_pass`

### `database.py`

- `DatabaseManager`: `__init__`, `_connect`, `_create_schema`, `get_app_state`, `set_app_state`, `create_task`, `update_task`, `delete_task`, `update_overdue_statuses`, `get_tasks_filtered`, `get_stats`, `clear_archived_tasks`, `get_task`, `get_all_tasks`, `get_archived_tasks`, `count_tasks`, `_row_to_task`

### `models.py`

- `Task` (dataclass)

### `services.py`

- `TaskService`: `__init__`, `initialize_demo_data`, `_is_demo_data_initialized`, `_mark_demo_data_initialized`, `get_tasks`, `get_task`, `get_archived_tasks`, `save_task`, `delete_task`, `clear_archived_tasks`, `find_tasks_by_title`, `mark_task_done`, `update_overdue_tasks`, `get_statistics`, `create_task_from_ai`, `delete_task_from_ai`, `mark_task_done_from_ai`, `update_task_from_ai`, `list_tasks_for_ai`, `get_statistics_for_ai`, `_task_to_ai_dict`, `_build_candidates_answer`, `_priority_from_ai`, `_normalize_search_tokens`, `calculate_status`, `parse_date`, `parse_time`, `parse_due_datetime`, `get_next_due_date`, `get_countdown_text`, `_validate_task_data`

### `ai_config.py`

- `AISettings`: `is_configured`, `from_env`

### `ai_date_parser.py`

- `ParsedDateContext` (dataclass)
- функции: `_start_of_week`, `_end_of_week`, `_next_weekday`, `extract_time`, `extract_absolute_date`, `parse_relative_datetime`, `build_relative_date_hints`

### `ai_agent.py`

- `AgentCommand` (dataclass)
- `AssistantReply` (dataclass)
- `BaseLLMClient`: `complete`
- `OpenAIClient`: `__init__`, `complete`
- `TaskCommandDispatcher`: `__init__`, `dispatch`, `_build_ui_hints`
- `TaskAIAgent`: `__init__`, `process_message`, `analyze_message`, `_load_local_action_model`, `_try_local_action_command`, `_local_action_matches_text`, `_predict_local_action`, `_load_local_intent_model`, `_try_local_intent_command`, `_predict_local_intent_action`, `_build_forced_create_command`, `_build_forced_delete_command`, `_build_forced_list_command`, `_build_forced_mark_done_command`, `_build_forced_update_command`, `_build_user_prompt`, `_parse_llm_command`, `_load_json_payload`, `_sanitize_command`, `_sanitize_create_data`, `_normalize_due_date_string`, `_heuristic_command`, `_try_direct_create_command`, `_infer_priority`, `_looks_garbled`, `_sanitize_agent_command`, `_sanitize_assistant_reply`, `_extract_title_query_for_action`, `_infer_recurrence`, `_infer_category`, `_infer_title`, `_infer_description`, `_heuristic_update_command`, `_has_update_changes`, `_looks_like_implicit_task`, `_remember_pending_resolution`, `_try_resolve_pending`, `_select_candidate_from_message`, `_looks_like_new_command`, `_handle_active_wizard`, `_begin_update_flow`, `_start_update_wizard`, `_start_create_wizard`, `_handle_create_wizard`, `_handle_update_wizard`, `_reply_for_create_step`, `_reply_for_update_step`, `_build_update_changes_payload`, `_make_wizard_reply`, `_next_create_reply`, `_build_time_choice_reply`, `_build_priority_reply`, `_parse_priority_from_text`, `_parse_due_date_from_text`, `_task_to_candidate`, `_build_candidate_prompt`, `_task_to_wizard_draft`, `_extract_month_only`, `_month_to_genitive`, `_parse_time_from_text`, `_text_has_explicit_time`, `_apply_time_to_due_date`, `_normalize_due_without_time`, `_cleanup_title`, `_strip_task_noise`, `_remove_obscene_words`, `_normalize_named_phrase`, `_sentence_case`, `_looks_like_cancel_command`, `_due_date_has_custom_time`, `_format_draft_preview`

### `ui/components.py`

- функции: `_capsule_radius`, `bind_text_size`, `bind_auto_height`
- `MaterialRoot`: `__init__`, `_update_canvas`
- `MaterialCard`: `__init__`, `set_palette`, `_update_canvas`
- `MaterialButton`: `__init__`, `set_palette`, `_update_state`, `_update_canvas`
- `FilledButton`: `__init__`
- `DangerButton`: `__init__`
- `MaterialTextInput`: `__init__`, `_update_canvas`
- `SpinnerOptionMaterial`: `__init__`
- `MaterialSpinner`: `__init__`, `_update_canvas`
- `Chip`: `__init__`, `_update_size`, `_update_canvas`
- `CircleButton`: `__init__`
- `IconCircleButton`: `__init__`, `_update_icon`
- `MaterialLabel`: `__init__`

### `ui/screens.py`

- `TaskRow`: `__init__`, `_fill`, `_build`
- `TaskListScreen`: `__init__`, `_build_ui`, `toggle_filters`, `apply_filters`, `_open_chat`, `refresh_tasks`, `reset_filters`, `open_task_form`, `save_task`, `complete_task`, `confirm_delete`, `_delete_and_close`
- `ArchiveScreen`: `__init__`, `_build_ui`, `refresh_archive`, `_delete_archived`, `_clear_all_archive`

### `ui/forms.py`

- `TaskFormPopup`: `__init__`, `_build_content`, `_field`, `_date_field`, `_time_field`, `_open_date_picker`, `_open_time_picker`, `_on_date_selected`, `_on_time_selected`, `_clear_date`, `_clear_time`, `_fill_data`, `_save`

### `ui/chat_screen.py`

- `ChatBubble`: `__init__`
- `ChatModal`: `__init__`, `_build_ui`, `send_message`, `_worker`, `_on_reply`, `_on_error`, `_set_busy`, `_append_message`, `_build_draft_card`, `_build_status_line`, `_scroll_bottom`

### `ui/android_pickers.py`

- функции: `_is_android`, `open_date_picker`, `open_time_picker`

### `scripts/prepare_massive_ru.py`

- `parse_args`, `_pick_column`, `_write_jsonl`, `main`

### `scripts/train_intent_model.py`

- `parse_args`, `read_jsonl`, `to_xy`, `main`

### `scripts/eval_intent_model.py`

- `parse_args`, `read_jsonl`, `to_xy`, `main`

### `scripts/generate_action_router_dataset.py`

- `_append_create`, `_append_delete`, `_append_done`, `_append_update`, `_append_list`, `_append_stats`, `_append_clarify`, `_dedupe`, `_write_jsonl`, `main`

### `scripts/train_action_router.py`

- `parse_args`, `read_jsonl`, `to_xy`, `main`

### `scripts/eval_action_router.py`

- `parse_args`, `read_jsonl`, `to_xy`, `main`

### `scripts/show_active_llm.py`

- `main`

---

## 11) Ограничения и замечания

1. Юнит/интеграционные тесты (pytest) в проекте отсутствуют; контроль качества через CLI-оценку моделей и ручную проверку UI.
2. `guaranteed_phrases_ru.txt` в коде сейчас не используется импортом.
3. `data/`, `models/`, `reports/`, `tasks.db` игнорируются `.gitignore`, но могут присутствовать локально как рабочие артефакты.
4. Для внешнего LLM нужен API-ключ и корректные env-переменные.

---

## 12) Минимальный запуск

```bash
python -m pip install -r requirements.txt
python main.py
```

Для NLU/ML пайплайна:

```bash
python -m pip install -r requirements-nlu.txt
python scripts/prepare_massive_ru.py --config ru-RU
python scripts/train_intent_model.py
python scripts/eval_intent_model.py
python scripts/generate_action_router_dataset.py
python scripts/train_action_router.py
python scripts/eval_action_router.py
```
