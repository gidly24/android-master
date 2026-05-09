# Приложение для контроля сроков регулярных пользовательских задач

Учебный MVP-проект на Python для ВКР. Приложение помогает вести локальный список регулярных задач, отслеживать сроки, отмечать выполнение, искать и фильтровать задачи, а также просматривать простую статистику.

## Стек

- Python 3.11+
- Kivy
- SQLite (`sqlite3` входит в стандартную библиотеку Python)

## Структура проекта

```text
PythonProject/
├─ main.py
├─ database.py
├─ models.py
├─ services.py
├─ requirements.txt
├─ README.md
├─ .gitignore
└─ ui/
   ├─ __init__.py
   ├─ components.py
   ├─ forms.py
   └─ screens.py
```

## Что реализовано

- добавление задачи;
- редактирование задачи;
- удаление задачи;
- просмотр списка задач;
- поиск по названию;
- фильтрация по статусу и категории;
- автоматическое определение просроченных задач;
- отметка выполнения;
- пересчет даты для периодических задач;
- экран статистики;
- локальное хранение в SQLite;
- тестовые задачи при первом запуске.

## Категории задач

- лекарства
- платежи
- бытовые дела
- подписки
- другое

## Параметры задачи

- название;
- описание;
- категория;
- дата ближайшего выполнения;
- периодичность;
- приоритет;
- статус.

## Логика периодических задач

Если задача периодическая и пользователь нажимает кнопку `Выполнено`, приложение не завершает ее окончательно, а переносит на следующий период:

- `ежедневно` - +1 день;
- `еженедельно` - +7 дней;
- `ежемесячно` - следующий месяц с корректировкой числа, если такого дня нет.

Для одноразовой задачи статус меняется на `выполнена`, без пересчета даты.

## Определение просроченных задач

Перед выводом списка и статистики приложение сравнивает `due_date` с текущей датой:

- если дата уже прошла, задача получает статус `просрочена`;
- если дата сегодня или позже, задача считается `активна`;
- задачи со статусом `выполнена` не переводятся обратно.

## База данных

Используется локальная таблица `tasks` со следующими полями:

- `id`
- `title`
- `description`
- `category`
- `due_date`
- `recurrence`
- `priority`
- `status`
- `created_at`
- `updated_at`

## Запуск проекта

1. Откройте проект в PyCharm.
2. Выберите интерпретатор Python 3.11 или новее.
3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Запустите файл `main.py`.

## Примечания

- Интерфейс сделан в темной теме.
- Подписи интерфейса выполнены на русском языке.
- Названия классов и переменных оставлены на английском.
- Данные хранятся только локально.
- Файл `tasks.db` не добавляется в Git, поэтому при первом запуске на новом компьютере тестовые задачи создадутся автоматически.
## NLU (MASSIVE ru-RU)

Install NLU dependencies:

```bash
python -m pip install -r requirements-nlu.txt
```

Prepare dataset:

```bash
python scripts/prepare_massive_ru.py --config ru-RU
```

Train baseline intent model:

```bash
python scripts/train_intent_model.py
```

Evaluate on test split:

```bash
python scripts/eval_intent_model.py
```

Generate local action dataset:

```bash
python scripts/generate_action_router_dataset.py
```

Train local action router:

```bash
python scripts/train_action_router.py
```

Evaluate local action router:

```bash
python scripts/eval_action_router.py
```

Check active LLM model for app answers:

```bash
python scripts/show_active_llm.py
```

Main artifacts:

- `data/nlu_train.jsonl`
- `data/nlu_validation.jsonl`
- `data/nlu_test.jsonl`
- `data/nlu_metadata.jsonl`
- `models/intent_model.joblib`
- `reports/train_report.txt`
- `reports/eval_report.txt`
- `reports/eval_errors.jsonl`
- `data/action_router_train.jsonl`
- `data/action_router_validation.jsonl`
- `models/action_router.joblib`
- `reports/action_router_report.txt`
- `reports/action_router_eval.txt`
- `reports/action_router_errors.jsonl`

Use local intent model in runtime (`ai_agent.py`):

```powershell
# enabled by default when models/intent_model.joblib exists
$env:TASK_LOCAL_INTENT_ENABLED="1"
$env:TASK_LOCAL_INTENT_MIN_CONFIDENCE="0.55"
$env:TASK_LOCAL_ACTION_ENABLED="1"
$env:TASK_LOCAL_ACTION_MIN_CONFIDENCE="0.55"

# optional custom model path
$env:TASK_INTENT_MODEL_PATH="models/intent_model.joblib"
$env:TASK_ACTION_MODEL_PATH="models/action_router.joblib"
```
