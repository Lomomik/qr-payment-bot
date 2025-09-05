# Деплой на Fly.io

## Преимущества Fly.io
✅ **$5 в месяц кредитов бесплатно** (покрывает небольшого бота)
✅ **Работает 24/7**
✅ **Быстрый деплой**
✅ **Автоскейлинг**
✅ **CLI инструменты**

## Пошаговая инструкция

### Шаг 1: Установка Fly CLI
```powershell
# Через PowerShell (Windows)
iwr https://fly.io/install.ps1 -useb | iex
```

### Шаг 2: Создайте Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "qr.py"]
```

### Шаг 3: Создайте fly.toml
```toml
app = "qr-payment-bot-unique-name"
primary_region = "fra"

[build]

[env]
  PORT = "8000"

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[processes]
  app = "python qr.py"
```

### Шаг 4: Деплой
```powershell
# Авторизация
fly auth login

# Инициализация проекта
fly launch --no-deploy

# Установка переменных окружения
fly secrets set BOT_TOKEN="ваш-токен"
fly secrets set ADMIN_TELEGRAM_ID="ваш-id"
fly secrets set OWNER_NAME="имя-получателя"
fly secrets set ACCOUNT_NUMBER="номер-счета"

# Деплой
fly deploy
```

### Шаг 5: Мониторинг
```powershell
# Просмотр логов
fly logs

# Статус приложения
fly status

# Подключение к консоли
fly ssh console
```

## Особенности
- Первые $5/месяц бесплатно
- Автоматическое масштабирование
- Глобальные регионы
- Встроенный мониторинг
