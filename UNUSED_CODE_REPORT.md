# Отчет о неиспользуемом коде в проекте Task Control

Дата: 28 мая 2026 г.

## Резюме

В проекте найдены **2 неиспользуемых компонента** в файле `ui/components.py`:

---

## Неиспользуемые компоненты

### 1. **Класс `SpinnerOptionMaterial`** (ui/components.py, строка ~240)

**Статус:** ❌ Не используется

**Описание:** Кастомный класс для опций спиннера с Material Design стилем.

**Где определен:**
```python
class SpinnerOptionMaterial(SpinnerOption):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", POPUP_SURFACE)
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
```

**Почему не используется:**
- Определен в `MaterialSpinner` как `option_cls=SpinnerOptionMaterial`
- Однако **не экспортируется** из `components.py` (нет в импортах других файлов)
- Используется только внутри `MaterialSpinner` класса

**Рекомендация:** Оставить как есть (это внутренний класс для `MaterialSpinner`), или удалить если не планируется использовать отдельно.

---

### 2. **Функция `_capsule_radius()`** (ui/components.py, строка ~40)

**Статус:** ❌ Не экспортируется, но используется внутри

**Описание:** Вспомогательная функция для расчета радиуса скругления.

**Где определена:**
```python
def _capsule_radius(size, fallback_radius=None):
    max_radius = max(min(size[0], size[1]) / 2, 0)
    if fallback_radius is None:
        return max_radius
    return min(fallback_radius, max_radius)
```

**Где используется:**
- `MaterialCard._update_canvas()` — строка ~120
- `MaterialButton._update_canvas()` — строка ~180
- `MaterialTextInput._update_canvas()` — строка ~260
- `MaterialSpinner._update_canvas()` — строка ~290
- `Chip._update_canvas()` — строка ~330
- `IconCircleButton._update_canvas()` — строка ~370

**Статус:** ✅ Используется внутри файла (приватная функция)

**Рекомендация:** Оставить как есть.

---

## Полностью используемые компоненты

✅ **Классы:**
- `MaterialRoot` — используется в `main.py`
- `MaterialCard` — используется в `ui/forms.py`, `ui/screens.py`
- `MaterialButton` — используется в `ui/forms.py`, `ui/screens.py`
- `FilledButton` — используется в `ui/screens.py`
- `DangerButton` — используется в `ui/forms.py`
- `MaterialTextInput` — используется в `ui/forms.py`, `ui/screens.py`
- `MaterialSpinner` — используется в `ui/forms.py`, `ui/screens.py`
- `Chip` — используется в `ui/screens.py`
- `CircleButton` — используется в `ui/screens.py`
- `IconCircleButton` — используется в `ui/screens.py`
- `MaterialLabel` — используется в `ui/forms.py`, `ui/screens.py`

✅ **Функции:**
- `bind_text_size()` — используется в `ui/forms.py`, `ui/screens.py`
- `bind_auto_height()` — используется в `ui/forms.py`, `ui/screens.py`

---

## Другие файлы

### `ai_assistant.py`
- ✅ Все методы используются
- Класс `AIAssistant` полностью функционален

### `database.py`
- ✅ Все методы используются
- Класс `DatabaseManager` полностью функционален

### `services.py`
- ✅ Все публичные методы используются
- Приватные методы (начинающиеся с `_`) используются внутри класса

### `models.py`
- ✅ Класс `Task` используется везде
- ✅ Все константы используются

### `main.py`
- ✅ Все методы используются

### `ui/forms.py`
- ✅ Класс `TaskFormPopup` используется в `ui/screens.py`

### `ui/screens.py`
- ✅ Классы `TaskListScreen`, `ArchiveScreen`, `FilterModal`, `TaskRow` используются в `main.py`

### `ui/chat_screen.py`
- ✅ Класс `ChatModal` используется в `main.py`

### `ui/android_pickers.py`
- ✅ Функции `open_date_picker()`, `open_time_picker()` используются в `ui/forms.py`

---

## Выводы

**Хорошие новости:**
- Проект хорошо организован
- Нет явно мертвого кода
- Все основные компоненты используются

**Рекомендации:**
1. `SpinnerOptionMaterial` — это приватный класс для `MaterialSpinner`, можно переименовать в `_SpinnerOptionMaterial` для ясности
2. Все остальное в порядке

**Общая оценка:** ✅ Код чистый и хорошо структурирован
