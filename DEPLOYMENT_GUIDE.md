# 🚀 Руководство по развертыванию QR Payment Bot

## 📋 Содержание
1. [Развертывание на Render.com](#render-deployment)
2. [Решение проблемы засыпания на Render](#render-sleep-fix)
3. [Альтернативные платформы](#alternative-platforms)
4. [Локальное тестирование](#local-testing)

---

## 🎯 Render.com Deployment {#render-deployment}

### Быстрый старт

1. **Подготовка репозитория:**
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Создание Web Service на Render:**
   - Зайдите на https://render.com
   - New → Web Service
   - Подключите ваш GitHub репозиторий
   - Настройки:
     - **Name:** `qr-payment-bot`
     - **Region:** Frankfurt
     - **Branch:** `main`
     - **Runtime:** Python 3
     - **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
     - **Start Command:** `python qr.py`

3. **Настройка переменных окружения:**
   В разделе Environment добавьте:
   ```
   BOT_TOKEN=ваш_токен_бота
   ADMIN_TELEGRAM_ID=ваш_telegram_id
   OWNER_NAME=ULIANA EMELINA
   ACCOUNT_NUMBER=3247217010/3030
   IBAN=CZ3230300000003247217010
   RENDER_EXTERNAL_URL=https://ваше-приложение.onrender.com
   ```

4. **Deploy:**
   - Нажмите "Create Web Service"
   - Дождитесь завершения деплоя (2-5 минут)

### Автоматический деплой

Render автоматически пересобирает и деплоит при каждом push в GitHub.

### Health Check

В `render.yaml` настроен health check:
```yaml
healthCheckPath: /health
```

Бот автоматически создает `/health` endpoint через `render_keep_alive.py`.

---

## 🔧 Решение проблемы засыпания {#render-sleep-fix}

### 🚨 Проблема
Render Free Plan переводит сервисы в "сон" после 15 минут неактивности, что вызывает задержки до 50 секунд.

### ✅ Решение (встроено в бот)

Бот использует встроенную систему keep-alive из модуля `render_keep_alive.py`:

**Как работает:**
1. Создается HTTP сервер с `/health` endpoint на порту 8080
2. Бот пингует сам себя каждые 5 минут
3. Это предотвращает "засыпание" сервиса

**Уже настроено в `qr.py`:**
```python
from render_keep_alive import setup_render_keep_alive, render_keep_alive

# В функции run_bot():
if os.getenv('RENDER') and setup_render_keep_alive:
    keep_alive_coro = setup_render_keep_alive()
    keep_alive_task = asyncio.create_task(keep_alive_coro)
```

### 🆙 Альтернативные решения

#### 1. UptimeRobot (внешний мониторинг)
- Зарегистрируйтесь на https://uptimerobot.com/
- Добавьте ваш Render URL: `https://ваше-приложение.onrender.com/health`
- Установите интервал проверки: 5 минут
- **Преимущество:** Дополнительный мониторинг + keep-alive

#### 2. Render Paid Plan ($7/месяц)
- Сервис никогда не засыпает
- Лучшая производительность
- 100% uptime

---

## 🌍 Альтернативные платформы {#alternative-platforms}

### Oracle Cloud Always Free (Рекомендуется)
- ✅ Навсегда бесплатно
- ✅ Не засыпает
- ✅ 1GB RAM, 1 OCPU
- ❌ Сложнее настройка

**Быстрая настройка:**
1. Создайте VM на Oracle Cloud
2. Установите Python и git
3. Клонируйте репозиторий
4. Настройте systemd service:
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
   ```ini
   [Unit]
   Description=QR Payment Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/qr-bot
   Environment="PATH=/home/ubuntu/qr-bot/venv/bin:/usr/bin"
   ExecStart=/home/ubuntu/qr-bot/venv/bin/python qr.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
5. Запустите сервис:
   ```bash
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   ```

### Railway ($5/месяц)
- ✅ Простое развертывание
- ✅ Не засыпает
- ✅ Автоматический SSL
- ❌ Нет бесплатного плана

### Fly.io
- ✅ 3 приложения бесплатно
- ✅ Глобальная сеть
- ⚠️ Ограниченные ресурсы

---

## 🖥️ Локальное тестирование {#local-testing}

### Установка зависимостей

```bash
# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### Настройка .env

Создайте файл `.env`:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=your_telegram_id_here
OWNER_NAME=ULIANA EMELINA
ACCOUNT_NUMBER=3247217010/3030
IBAN=CZ3230300000003247217010
```

### Запуск бота

```bash
# Production версия
python qr.py

# Тестовая версия (использует .env.test)
python qr_test.py
```

### Остановка бота

```bash
# Ctrl+C для graceful shutdown
# Бот автоматически очистит ресурсы и lock файлы
```

---

## 📊 Мониторинг

### Логи на Render
```bash
# В Dashboard → Logs
# Или через Render CLI:
render logs -s qr-payment-bot
```

### Проверка работы
```bash
# Проверка health endpoint
curl https://ваше-приложение.onrender.com/health
```

Ожидаемый ответ:
```json
{
  "status": "ok",
  "service": "qr-payment-bot",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## 🔒 Безопасность

1. **Никогда не коммитьте:**
   - `.env` файлы
   - Токены ботов
   - API ключи
   - Credentials файлы

2. **Используйте .gitignore:**
   ```
   .env
   .env.test
   .env.local
   credentials.json
   token.pickle
   ```

3. **Ротация токенов:**
   - Регулярно обновляйте токен бота через @BotFather
   - Обновляйте переменные окружения на Render

---

## 🆘 Troubleshooting

### Бот не отвечает на Render
1. Проверьте логи: `render logs`
2. Убедитесь что BOT_TOKEN правильный
3. Проверьте health endpoint
4. Перезапустите сервис: Dashboard → Manual Deploy → Deploy latest commit

### Конфликт "getUpdates"
Если видите ошибку `Conflict: terminated by other getUpdates request`:
1. Остановите все другие экземпляры бота
2. Дождитесь 30 секунд
3. Перезапустите на Render

Бот автоматически обрабатывает конфликты (см. `qr.py`, функция `run_bot()`).

### Бот засыпает на Render
Убедитесь что:
1. `render_keep_alive.py` импортируется в `qr.py`
2. `RENDER_EXTERNAL_URL` установлен в переменных окружения
3. Health endpoint доступен: `/health`

---

## 📞 Поддержка

Для вопросов и проблем:
- Проверьте логи
- Изучите секцию Troubleshooting
- Проверьте Issues на GitHub

---

**Версия:** 1.0  
**Последнее обновление:** 2024
