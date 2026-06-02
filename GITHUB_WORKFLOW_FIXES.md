# 🔧 GitHub Workflow - История исправлений

## Проблемы которые были решены

### Проблема 1: `libncurses5` не найден
**Ошибка:** `Unable to locate package libncurses5`

**Решение:** Заменить на `libncurses6` (старый пакет устарел)

### Проблема 2: Ошибка autoconf при сборке libffi
**Ошибка:**
```
autoreconf: error: /usr/bin/autoconf failed with exit status: 1
configure.ac:215: error: possibly undefined macro: LT_SYS_SYMBOL_USCORE
```

**Решение:** 
1. ✅ Добавить `libtool`, `autoconf`, `automake`, `m4`
2. ✅ Использовать Docker контейнер (ubuntu:22.04) для стабильного окружения
3. ✅ Установить полный набор autotools (`gettext`, `texinfo`)
4. ✅ Pinned Cython на `0.29.36` (более стабильная версия с buildozer)

### Проблема 3: Несовместимость Java версий
**Решение:** Явно установить `JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64`

---

## Финальная конфигурация

### Docker контейнер: `ubuntu:22.04`
✅ Полный контроль над окружением  
✅ Гарантированные версии зависимостей  
✅ Нет сюрпризов с система обновлениями  

### Установленные пакеты
```
python3, openjdk-11, build-essential
libtool, autoconf, automake, m4
libffi-dev, libssl-dev, texinfo, gettext
libsdl2-dev и другие media библиотеки
```

### Версии
- **Java:** OpenJDK 11
- **Python:** 3.10 (в ubuntu:22.04)
- **Cython:** 0.29.36 (pinned для стабильности)
- **Buildozer:** latest

### Переменные окружения
```bash
GRADLE_OPTS: -Xmx2048m -XX:+HeapDumpOnOutOfMemoryError
JAVA_OPTS: -Xmx2048m
JAVA_HOME: /usr/lib/jvm/java-11-openjdk-amd64
PATH: /usr/lib/ccache:$PATH (для кэширования)
```

---

## Ожидаемые результаты

### Первая сборка
- ⏱️ **30-45 минут** (gradle качает весь SDK)
- 📦 Готовый `taskcontrol-1.0-debug.apk`

### Последующие сборки
- ⏱️ **15-25 минут** (кэш gradle)
- 📦 Готовый APK с кэшем

---

## Если всё ещё падает

### Проверь в логах:
1. Ищи `ERROR` или `failed`
2. Обычно это проблема в:
   - `buildozer.spec` (конфиг)
   - `requirements.txt` (зависимости)
   - `main.py` или другом коде (синтаксис)

### Типичные ошибки
- **ImportError** - проблема в импортах Python
- **Gradle error** - проблема в gradle конфиге
- **Cython error** - проблема в C расширениях

### Решение
Скопируй последние 100 строк лога и покажи мне.

---

## Альтернативные решения (если не сработает)

### Вариант 1: Использовать python 3.9 вместо 3.10
```yaml
container:
  image: python:3.9-slim
```

### Вариант 2: Использовать готовый Kivy Docker image
```yaml
container:
  image: kivy/kivy:latest
```

### Вариант 3: Использовать WSL2 локально
На Windows 11 это быстрее и проще чем GitHub Actions

---

## Полезные ссылки

- **GitHub Actions docs:** https://docs.github.com/en/actions
- **Buildozer docs:** https://buildozer.readthedocs.io/
- **Python-for-Android:** https://python-for-android.readthedocs.io/

---

Последний commit: `f1f2988` 🎯
