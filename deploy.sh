#!/bin/bash
# Скрипт для быстрого развертывания бота

echo "🎯 Развертывание Telegram бота на Oracle Cloud..."

# Проверка что мы в правильной директории
if [ ! -f "qr.py" ]; then
    echo "❌ Файл qr.py не найден! Убедитесь что вы в директории с ботом."
    exit 1
fi

# Активация виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создаем виртуальное окружение..."
    python -m venv venv
fi

source venv/bin/activate

# Установка зависимостей
echo "📥 Устанавливаем зависимости..."
pip install -r requirements.txt

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создайте файл .env с содержимым:"
    echo "BOT_TOKEN=your_bot_token_here"
    echo "ADMIN_TELEGRAM_ID=your_telegram_id_here"
    echo "OWNER_NAME=ULIANA EMELINA"
    echo "ACCOUNT_NUMBER=3247217010/3030"
    exit 1
fi

# Установка systemd сервиса
echo "⚙️  Настраиваем systemd сервис..."
sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot

# Запуск сервиса
echo "🚀 Запускаем бота..."
sudo systemctl start telegram-bot

# Проверка статуса
sleep 3
echo "📊 Статус сервиса:"
sudo systemctl status telegram-bot --no-pager

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "🔧 Полезные команды:"
echo "  Просмотр логов:    sudo journalctl -u telegram-bot -f"
echo "  Перезапуск:        sudo systemctl restart telegram-bot"
echo "  Остановка:         sudo systemctl stop telegram-bot"
echo "  Статус:            sudo systemctl status telegram-bot"
echo ""
echo "🌐 Ваш бот должен быть онлайн в Telegram!"
