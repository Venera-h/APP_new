#!/bin/bash
# Скрипт для установки зависимостей
# Запустите: chmod +x install.sh && ./install.sh

echo "Установка зависимостей для React клиента..."

# Проверяем наличие pnpm
if command -v pnpm &> /dev/null; then
    echo "Используем pnpm..."
    pnpm install
elif command -v npm &> /dev/null; then
    echo "Используем npm..."
    npm install
elif command -v yarn &> /dev/null; then
    echo "Используем yarn..."
    yarn install
else
    echo "Ошибка: Не найден ни один пакетный менеджер (pnpm, npm, yarn)"
    echo "Установите Node.js и npm с официального сайта: https://nodejs.org/"
    exit 1
fi

echo "Зависимости установлены!"
echo "Для запуска используйте:"
echo "  pnpm dev  или  npm run dev  или  yarn dev"