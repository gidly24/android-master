# 🔨 Инструкция по сборке Android приложения

## ❌ Что я исправил в buildozer.spec

1. **Зависимости** - удалил `openssl` (часто вызывает конфликты)
2. **Requirements.txt** - добавил `certifi` явно
3. **Gradle** - добавил правильные репозитории (`google()`, `mavenCentral()`)
4. **Packaging** - упростил опции исключения (убрал дублирующиеся)
5. **Архитектуры** - пока только `arm64-v8a` для быстрой сборки (позже добавить `armeabi-v7a`)
6. **Мусор** - очистил странный текст в комментариях

## 📋 Шаги для сборки

### Шаг 1: Очистка кэша (ОЧЕНЬ ВАЖНО!)
```bash
bash clean_build.sh
```
Или вручную:
```bash
rm -rf .buildozer build bin dist __pycache__ .gigacode
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

### Шаг 2: Установка зависимостей (только первый раз)
```bash
pip install -r requirements.txt
pip install buildozer cython
```

### Шаг 3: Сборка Debug версии (для тестирования)
```bash
buildozer android debug
```

**Первый раз будет долго (20-40 минут)** - buildozer скачивает SDK, NDK, градл и всё остальное.

### Шаг 4: Установка на телефон
```bash
buildozer android debug deploy run
```

### Для Release версии (когда всё работает)
```bash
buildozer android release
```

## ⚠️ Если всё ещё падает, попробуй это:

1. **Полная переустановка окружения:**
```bash
rm -rf .buildozer .venv
python -m venv .venv
# Windows
.venv\Scripts\activate
# или Linux/Mac
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install buildozer cython
```

2. **Проверь версии:**
```bash
python --version  # должна быть 3.9+
buildozer --version
```

3. **Если ошибка про p4a (python-for-android):**
```bash
buildozer android debug 2>&1 | tail -50
```
Скопируй последние 50 строк ошибки и покажи мне.

## 🔍 Что смотреть в логах

Обычно buildozer пишет очень много текста. Ищи:
- ❌ `ERROR` - прямые ошибки
- ❌ `failed to build` - ошибки сборки
- ❌ `conflict` - конфликты зависимостей
- ⚠️ `WARNING` - может быть причиной проблем

## 📝 Если проблема в конкретном месте

Пришли мне последние 100 строк лога и я помогу диагностировать.

Запусти так (сохранит лог в файл):
```bash
buildozer android debug > build.log 2>&1
# Потом покажи последние 100 строк:
tail -100 build.log
```

## ✅ Когда сборка прошла успешно

- Найдёшь APK в `bin/` директории
- Он называется примерно `taskcontrol-1.0-debug.apk`
- Можешь установить его на телефон через `adb` или просто передать файл

Успехов! 🚀
