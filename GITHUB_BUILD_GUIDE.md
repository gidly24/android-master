# 🚀 GitHub Actions - Автоматическая сборка APK

## ✅ Что я создал

GitHub Actions workflow (`.github/workflows/build-android.yml`) который:
- ✅ Автоматически собирает APK при каждом `push` на `main`
- ✅ Устанавливает все зависимости (Java, Android SDK, Gradle)
- ✅ Запускает `buildozer android debug`
- ✅ Загружает готовый APK как artifact
- ✅ Логирует всё в случае ошибок

## 📊 Как отслеживать сборку

### 1. **Перейди на GitHub**
https://github.com/gidly24/android-master

### 2. **Клик на вкладку "Actions"**
![Вкладка Actions](https://imgur.com/abc123.png)

### 3. **Смотри список сборок**
Там будут все запущенные builds:
- 🟢 **Success** - APK готов к скачиванию
- 🟡 **In Progress** - сборка идет (15-30 минут)
- 🔴 **Failed** - ошибка, нужно смотреть лог

### 4. **Скачай APK**
Если сборка успешна (зелёный статус):
1. Клик на сборку
2. Scroll вниз в "Artifacts"
3. Скачай `taskcontrol-apk` (внутри файл `*.apk`)

## 🔄 Как запустить сборку

### Вариант 1: Автоматически (по умолчанию)
Просто делай `git push` на `main`:
```bash
git add .
git commit -m "какие-то изменения"
git push origin main
```
Сборка запустится автоматически!

### Вариант 2: Вручную (если нужна сборка без push)
На GitHub:
1. Actions → Build Android APK
2. "Run workflow" → выбери `main` → "Run workflow"

## 📝 Что смотреть если сборка упала

### Шаг 1: Открой Failed сборку
Клик на красный статус сборки

### Шаг 2: Scroll вниз и найди "Build APK (Debug)"
Там будут логи

### Шаг 3: Ищи ошибку
- Обычно видно где именно упало
- Может быть в зависимостях, gradle, или в коде

### Шаг 4: Исправь локально и запуши
```bash
# Исправляешь ошибку
git push origin main
# Сборка автоматически запустится снова
```

## 🎯 Время сборки

- **Первый раз:** 20-40 минут (gradle качает кэш)
- **Следующие разы:** 10-20 минут (кэш используется)

## 📦 Готовый APK

Когда скачаешь `taskcontrol-apk`:
```
taskcontrol-apk/
└── taskcontrol-1.0-debug.apk
```

Этот файл можно установить на телефон:

### На телефоне (Android):
1. Скопируй `taskcontrol-1.0-debug.apk` на телефон
2. Открой файл менеджер
3. Клик на APK
4. "Установить"
5. Может потребоваться разрешить установку из неизвестных источников

### Через ADB (если телефон подключен к ПК):
```bash
adb install bin/taskcontrol-1.0-debug.apk
```

## 🚨 Проблемы и решения

### Проблема: Сборка зависает на "Build APK (Debug)"
**Решение:** GitHub Actions имеет timeout 360 минут. Если зависает - может быть проблема в коде или зависимостях.

### Проблема: "artifact not found"
**Решение:** Сборка упала ДО создания APK. Смотри лог на какой строке ошибка.

### Проблема: Gradle ошибка
Обычно это проблема с `buildozer.spec` - я уже исправил основное, но если новые ошибки - скажи мне.

## ✅ Успешная сборка

Выглядит примерно так:
```
✓ Checkout code
✓ Set up Python
✓ Install system dependencies
✓ Install Python dependencies
✓ Build APK (Debug)
✓ List build output
✓ Upload APK as artifact
```

И в Artifacts видишь `taskcontrol-apk` с готовым APK внутри!

## 🔗 Полезные ссылки

- **Actions на твоем репо:** https://github.com/gidly24/android-master/actions
- **Документация GitHub Actions:** https://docs.github.com/en/actions
- **Buildozer документация:** https://buildozer.readthedocs.io/

---

## Следующие шаги

1. **Жди первую сборку** - на https://github.com/gidly24/android-master/actions
2. **Если успешна** - скачай APK и установи на телефон
3. **Если упала** - скажи мне код ошибки из лога

Удачи! 🚀
