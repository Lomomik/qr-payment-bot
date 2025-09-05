# Деплой на Koyeb

## Преимущества Koyeb
✅ **$5.50 кредитов в месяц**
✅ **Автодеплой из GitHub**
✅ **Не засыпает**
✅ **Простая настройка**
✅ **Быстрый старт**

## Пошаговая инструкция

### Шаг 1: Подготовка файлов
Создайте `requirements.txt`:
```
python-telegram-bot==21.4
qrcode[pil]==7.4.2
python-dotenv==1.0.1
```

### Шаг 2: Регистрация
1. Идите на https://koyeb.com
2. Регистрируйтесь через GitHub
3. Подтвердите email

### Шаг 3: Создание приложения
1. Нажмите "Create App"
2. Выберите "GitHub" как источник
3. Выберите ваш репозиторий
4. Настройте:
   - Name: qr-payment-bot
   - Branch: main
   - Build command: pip install -r requirements.txt
   - Run command: python qr.py

### Шаг 4: Переменные окружения
Добавьте в разделе Environment Variables:
- `BOT_TOKEN`
- `ADMIN_TELEGRAM_ID`
- `OWNER_NAME`
- `ACCOUNT_NUMBER`

### Шаг 5: Деплой
Нажмите "Deploy" - приложение автоматически задеплоится.

## Мониторинг
- Логи в реальном времени
- Метрики производительности
- Автоматический рестарт
- Уведомления о статусе
