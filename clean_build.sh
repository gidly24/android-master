#!/bin/bash

# Полная очистка buildozer
echo "🧹 Очищаем кэш buildozer..."
rm -rf .buildozer build bin dist __pycache__ .gigacode

# Очищаем Python кэш
echo "🗑️ Очищаем Python кэш..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Очищаем .venv если нужно
echo "⚠️  Если нужно - очистить .venv? Если yes, нужно переустановить зависимости"
# rm -rf .venv

echo ""
echo "✅ Очистка завершена!"
echo ""
echo "Теперь можно собирать:"
echo "buildozer android debug"
echo ""
echo "Или для release:"
echo "buildozer android release"
