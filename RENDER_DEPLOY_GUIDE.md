# 🚀 Пошаговая инструкция деплоя на Render.com

## ✅ Шаг 1: Подготовка (ЗАВЕРШЕН)
- [x] Создали qr_render.py с веб-сервером
- [x] Обновили requirements.txt (добавили aiohttp)
- [x] Создали render.yaml с конфигурацией
- [x] Закоммитили в Git и отправили на GitHub

## 🌐 Шаг 2: Регистрация на Render.com

### 2.1 Переходим на сайт
1. Откройте https://render.com в браузере
2. Нажмите **"Get Started for Free"**
3. Выберите **"Sign up with GitHub"**
4. Авторизуйтесь через ваш GitHub аккаунт

### 2.2 Подключаем репозиторий
1. После входа нажмите **"New +"** в правом верхнем углу
2. Выберите **"Web Service"**
3. Выберите **"Build and deploy from a Git repository"**
4. Найдите ваш репозиторий **"qr-payment-bot"** и нажмите **"Connect"**

## ⚙️ Шаг 3: Настройка Web Service

### 3.1 Базовые настройки
- **Name**: qr-payment-bot (или любое уникальное имя)
- **Region**: Frankfurt (Europe) - ближе к Чехии
- **Branch**: main
- **Root Directory**: оставьте пустым
- **Runtime**: Python 3

### 3.2 Build & Deploy
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `python qr_render.py`

### 3.3 Plan
- Выберите **"Free"** (0$/месяц, 750 часов)

## 🔐 Шаг 4: Переменные окружения

В разделе **"Environment Variables"** добавьте:

| Key | Value | Описание |
|-----|-------|----------|
| `BOT_TOKEN` | ваш токен от @BotFather | Токен Telegram бота |
| `ADMIN_TELEGRAM_ID` | ваш ID | ID администратора |
| `OWNER_NAME` | ULIANA EMELINA | Имя получателя |
| `ACCOUNT_NUMBER` | 3247217010/3030 | Номер счета |

> ⚠️ **Переменная `PORT` НЕ нужна** - Render автоматически установит нужный порт!

### Как получить BOT_TOKEN (если нужно):
1. Напишите @BotFather в Telegram
2. Отправьте /newbot или /token
3. Скопируйте токен формата: 123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw

### Как узнать свой TELEGRAM_ID:
1. Напишите @userinfobot в Telegram
2. Отправьте /start
3. Скопируйте ваш ID (число)

## 🚀 Шаг 5: Деплой

1. Нажмите **"Create Web Service"**
2. Render начнет автоматический деплой
3. Процесс займет 2-5 минут

## 📊 Шаг 6: Мониторинг

### 6.1 Проверка статуса
- В Dashboard вы увидите статус: "Live" (зеленый)
- URL вашего приложения: https://qr-payment-bot-xxxx.onrender.com

### 6.2 Проверка логов
- Перейдите в раздел **"Logs"**
- Вы должны увидеть:
  ```
  Web server started on port 10000
  Starting QR Payment Bot for Render...
  Bot application starting...
  ```

> 💡 **Зачем веб-сервер?** Render ожидает HTTP-ответы от приложений. Веб-сервер отвечает на health checks, чтобы Render знал, что бот работает. Без этого Render будет постоянно перезапускать приложение!

### 6.3 Тест health check
- Откройте ваш URL в браузере
- Вы должны увидеть: "Bot is running"

## ✅ Шаг 7: Тестирование бота

1. Найдите вашего бота в Telegram
2. Отправьте /start
3. Попробуйте создать QR-код
4. Убедитесь, что все работает

## 🔄 Автоматические обновления

Render автоматически обновляет бота при каждом push в main ветку GitHub!

## 📞 Поддержка

Если что-то не работает:
1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения заданы правильно
3. Проверьте, что BOT_TOKEN корректный

## 🎉 Готово!

Ваш бот теперь работает 24/7 на Render.com бесплатно!
