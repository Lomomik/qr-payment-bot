# Деплой на Oracle Cloud Always Free

## Преимущества Oracle Cloud
✅ **НАВСЕГДА БЕСПЛАТНО** (не пробный период)
✅ **2 VM с 1GB RAM каждая**
✅ **200GB хранилища**
✅ **10TB исходящего трафика**
✅ **Работает 24/7 без ограничений**

## Пошаговая инструкция

### Шаг 1: Регистрация
1. Идите на https://oracle.com/cloud/free
2. Регистрируйтесь (потребуется карта для верификации, но списаний не будет)
3. Выберите регион (например, Frankfurt)

### Шаг 2: Создание VM
1. В консоли OCI выберите "Compute" → "Instances"
2. Нажмите "Create Instance"
3. Выберите:
   - Shape: VM.Standard.E2.1.Micro (Always Free)
   - Image: Ubuntu 22.04
   - Network: создайте новую или используйте существующую

### Шаг 3: Настройка SSH
1. Скачайте приватный ключ
2. Подключитесь к серверу:
```bash
ssh -i private_key.pem ubuntu@your-vm-ip
```

### Шаг 4: Установка на сервере
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
sudo apt install python3 python3-pip python3-venv git -y

# Клонирование репозитория
git clone https://github.com/yourusername/qr-payment-bot.git
cd qr-payment-bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install python-telegram-bot==21.4 qrcode[pil]==7.4.2 python-dotenv==1.0.1

# Создание .env файла
nano .env
```

### Шаг 5: Настройка .env
```
BOT_TOKEN=ваш-токен-бота
ADMIN_TELEGRAM_ID=ваш-id
OWNER_NAME=имя-получателя
ACCOUNT_NUMBER=номер-счета
```

### Шаг 6: Создание systemd службы
```bash
sudo nano /etc/systemd/system/qr-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=QR Payment Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/qr-payment-bot
Environment=PATH=/home/ubuntu/qr-payment-bot/venv/bin
ExecStart=/home/ubuntu/qr-payment-bot/venv/bin/python qr.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Шаг 7: Запуск службы
```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable qr-bot

# Запуск службы
sudo systemctl start qr-bot

# Проверка статуса
sudo systemctl status qr-bot

# Просмотр логов
sudo journalctl -u qr-bot -f
```

### Шаг 8: Автообновление из GitHub
```bash
# Создайте скрипт обновления
nano update-bot.sh
```

```bash
#!/bin/bash
cd /home/ubuntu/qr-payment-bot
git pull origin main
sudo systemctl restart qr-bot
echo "Bot updated and restarted"
```

```bash
chmod +x update-bot.sh
```

## Особенности
- Навсегда бесплатно (не пробный период)
- Полный контроль над сервером
- Можно запускать несколько ботов
- SSH доступ
- Возможность установки дополнительного ПО
