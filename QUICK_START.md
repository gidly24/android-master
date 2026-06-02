# 🚀 Быстрый старт для сборки APK на GitHub

## За 3 минуты до готового APK

### Шаг 1: Запустить сборку 
https://github.com/gidly24/android-master/actions
1. Нажми "Build Android APK"
2. Нажми "Run workflow"
3. Выбери `main`
4. Нажми "Run workflow"

### Шаг 2: Ждать (~30-45 минут первый раз)
- 🟡 In Progress - сборка идет
- 🟢 Success - готово!
- 🔴 Failed - ошибка в логах

### Шаг 3: Скачать APK
1. Нажми на успешную сборку (зелёный статус)
2. Scroll вниз → "Artifacts"
3. Скачай `taskcontrol-apk` (ZIP)
4. Распакуй → `taskcontrol-1.0-debug.apk`

### Шаг 4: Установить на телефон
```bash
# На ПК:
adb install taskcontrol-1.0-debug.apk

# Или вручную на телефоне:
# 1. Скопировать файл на телефон
# 2. Открыть файл менеджер
# 3. Клик на APK → Установить
```

---

## Если сборка упала 🔴

### Быстрая диагностика
1. Клик на красный статус сборки
2. Scroll вниз → "Build APK (Debug)"
3. Ищи `ERROR:` или `failed`
4. Скопируй последние 50 строк

### Типичные ошибки и решения

| Ошибка | Решение |
|--------|---------|
| `LT_SYS_SYMBOL_USCORE` | ✅ Уже исправлено в workflow |
| `libncurses5 not found` | ✅ Уже заменено на libncurses6 |
| `ImportError` | Проверь `requirements.txt` |
| `Gradle error` | Проверь `buildozer.spec` |
| `SyntaxError` | Проверь Python код |

---

## Автоматическая сборка при push

Просто делай обычный git:
```bash
git add .
git commit -m "описание изменений"
git push origin main
```

Сборка запустится автоматически! ✨

---

## Документация

- 📖 [BUILD_GUIDE.md](BUILD_GUIDE.md) - подробная инструкция
- 📖 [GITHUB_BUILD_GUIDE.md](GITHUB_BUILD_GUIDE.md) - как отслеживать сборки
- 📖 [FAQ.md](FAQ.md) - часто задаваемые вопросы
- 📖 [FIX_CHANGELOG.md](FIX_CHANGELOG.md) - что я исправил в buildozer.spec
- 📖 [GITHUB_WORKFLOW_FIXES.md](GITHUB_WORKFLOW_FIXES.md) - история исправлений workflow

---

## Нужна помощь?

1. Проверь FAQ.md
2. Посмотри логи сборки
3. Прочитай GITHUB_WORKFLOW_FIXES.md

Готово! 🎉
