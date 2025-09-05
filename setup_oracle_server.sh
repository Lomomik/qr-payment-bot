#!/bin/bash
# Скрипт для автоматической настройки сервера Oracle Cloud

echo "🚀 Начинаем настройку сервера для Telegram бота..."

# Обновление системы
echo "📦 Обновляем систему..."
sudo dnf update -y

# Установка Python и необходимых пакетов
echo "🐍 Устанавливаем Python 3.9 и зависимости..."
sudo dnf install python39 python39-pip git nano htop -y

# Создание символических ссылок
sudo alternatives --install /usr/bin/python python /usr/bin/python3.9 1
sudo alternatives --install /usr/bin/pip pip /usr/bin/pip3.9 1

# Настройка firewall
echo "🔥 Настраиваем firewall..."
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload

# Создание директории проекта
echo "📁 Создаем директорию проекта..."
mkdir -p ~/telegram-bot
cd ~/telegram-bot

# Создание виртуального окружения
echo "🔨 Создаем виртуальное окружение..."
python -m venv venv
source venv/bin/activate

echo "✅ Базовая настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Загрузите файлы вашего бота в ~/telegram-bot/"
echo "2. Создайте файл .env с токенами"
echo "3. Запустите: pip install -r requirements.txt"
echo "4. Настройте systemd сервис"
echo ""
echo "💡 Директория проекта: ~/telegram-bot"
echo "💡 Активация venv: source ~/telegram-bot/venv/bin/activate"
