#!/bin/bash

# Скрипт для запуска бота на сервере
echo "Starting QR Payment Bot..."

# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python qr.py
