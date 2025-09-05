# Развертывание Telegram бота на Oracle Cloud Always Free

## Что вы получите бесплатно навсегда:
- 2 виртуальные машины с 1/8 OCPU и 1 ГБ памяти каждая
- 1 виртуальная машина Ampere A1 с 4 OCPU и 24 ГБ памяти
- 200 ГБ блочного хранилища
- 10 ГБ объектного хранилища

## Пошаговая инструкция

### Шаг 1: Создание аккаунта Oracle Cloud

1. Перейдите на https://oracle.com/cloud/free/
2. Нажмите "Start for free"
3. Заполните форму регистрации (потребуется кредитная карта для верификации, но списаний не будет)
4. Подтвердите email и номер телефона

### Шаг 2: Создание виртуальной машины

1. Войдите в Oracle Cloud Console
2. В меню выберите **Compute** → **Instances**
3. Нажмите **Create Instance**

#### Настройки инстанса:
- **Name**: `telegram-bot-server`
- **Image**: `Oracle Linux 8` (рекомендуется)
- **Shape**: 
  - Для Always Free: `VM.Standard.E2.1.Micro` (1/8 OCPU, 1GB RAM)
  - Или Ampere: `VM.Standard.A1.Flex` (до 4 OCPU, 24GB RAM бесплатно)
- **Primary VNIC**: оставьте по умолчанию
- **SSH Keys**: 
  - Выберите "Generate SSH Key Pair"
  - **Обязательно** сохраните приватный ключ!

4. Нажмите **Create**

### Шаг 3: Настройка Security List (открытие портов)

1. Перейдите в **Networking** → **Virtual Cloud Networks**
2. Выберите VCN вашего инстанса
3. Перейдите в **Security Lists** → **Default Security List**
4. Нажмите **Add Ingress Rules**

Добавьте правила:
- **Source CIDR**: `0.0.0.0/0`
- **IP Protocol**: `TCP`
- **Destination Port Range**: `80,443,8080`
- **Description**: `HTTP/HTTPS/Bot`

### Шаг 4: Подключение к серверу

1. Найдите публичный IP вашего инстанса в Console
2. Используйте SSH для подключения:

**Из Windows (PowerShell):**
```powershell
# Если у вас есть OpenSSH (Windows 10+)
ssh -i path\to\your\private\key opc@YOUR_PUBLIC_IP

# Или используйте PuTTY с конвертацией ключа
```

### Шаг 5: Установка необходимого ПО

После подключения к серверу выполните:

```bash
# Обновление системы
sudo dnf update -y

# Установка Python 3.9+ и pip
sudo dnf install python39 python39-pip git -y

# Создание символической ссылки для python
sudo alternatives --install /usr/bin/python python /usr/bin/python3.9 1
sudo alternatives --install /usr/bin/pip pip /usr/bin/pip3.9 1

# Установка firewall правил
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### Шаг 6: Загрузка и настройка бота

```bash
# Создание директории для проекта
mkdir ~/telegram-bot
cd ~/telegram-bot

# Клонирование репозитория (если у вас есть GitHub)
git clone https://github.com/YOUR_USERNAME/qr-payment-bot.git .

# Или создание файлов вручную (см. ниже)
```

### Шаг 7: Создание файлов проекта

Если вы не используете git, создайте файлы вручную:

```bash
# Создание основных файлов
nano qr.py  # Скопируйте содержимое из локального файла
nano requirements.txt
nano .env
```

### Шаг 8: Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 9: Настройка переменных окружения

Создайте файл `.env`:
```bash
nano .env
```

Содержимое:
```
BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=your_telegram_id_here
OWNER_NAME=ULIANA EMELINA
ACCOUNT_NUMBER=3247217010/3030
```

### Шаг 10: Создание systemd сервиса для автозапуска

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=Telegram QR Payment Bot
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/telegram-bot
Environment=PATH=/home/opc/telegram-bot/venv/bin
ExecStart=/home/opc/telegram-bot/venv/bin/python qr.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Шаг 11: Запуск сервиса

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-bot

# Запуск сервиса
sudo systemctl start telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot -f
```

## Управление сервисом

```bash
# Остановка
sudo systemctl stop telegram-bot

# Перезапуск
sudo systemctl restart telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot --no-pager -n 50
```

## Обновление бота

```bash
cd ~/telegram-bot
git pull  # если используете git
sudo systemctl restart telegram-bot
```

## Мониторинг ресурсов

```bash
# Использование памяти и CPU
htop

# Использование диска
df -h

# Логи системы
sudo journalctl -xe
```

## Преимущества Oracle Cloud Always Free:

1. **Навсегда бесплатно** - без временных ограничений
2. **Больше ресурсов** чем у других провайдеров
3. **Стабильность** Oracle Cloud Infrastructure
4. **Полный root доступ** к серверу
5. **Возможность установки любого ПО**

## Важные замечания:

- Аккаунт может быть заморожен при подозрительной активности
- Инстансы могут быть отключены при длительном простое (30+ дней без активности)
- Рекомендуется настроить мониторинг и регулярные проверки
- Всегда делайте бэкапы важных данных

## Сравнение с Railway:

| Параметр | Oracle Cloud Free | Railway ($5) |
|----------|-------------------|--------------|
| Стоимость | Бесплатно навсегда | $5/месяц |
| RAM | 1GB (до 24GB с Ampere) | ~500MB |
| CPU | 1/8 OCPU (до 4 OCPU) | Shared |
| Хранилище | 200GB | Ограничено |
| Время работы | 24/7 | 24/7 |
| Сложность | Средняя | Простая |
