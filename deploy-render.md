# Деплой на Render.com

## Преимущества Render
✅ **750 часов/месяц бесплатно** (достаточно для постоянной работы)
✅ **Автодеплой из GitHub**
✅ **Не засыпает** на бесплатном тарифе
✅ **Простая настройка**
✅ **Поддержка Python из коробки**

## Пошаговая инструкция

### Шаг 1: Подготовка файлов
Создайте в корне проекта файл `requirements.txt`:

```
python-telegram-bot==21.4
qrcode[pil]==7.4.2
python-dotenv==1.0.1
```

### Шаг 2: Создайте `render.yaml`
```yaml
services:
  - type: web
    name: qr-payment-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python qr.py
    envVars:
      - key: BOT_TOKEN
        sync: false
      - key: ADMIN_TELEGRAM_ID
        sync: false
      - key: OWNER_NAME
        sync: false
      - key: ACCOUNT_NUMBER
        sync: false
```

### Шаг 3: Регистрация на Render
1. Идите на https://render.com
2. Регистрируйтесь через GitHub
3. Подключите ваш репозиторий
4. Выберите "Web Service"
5. Настройте переменные окружения

### Шаг 4: Настройка переменных
В панели Render добавьте:
- `BOT_TOKEN` = ваш токен бота
- `ADMIN_TELEGRAM_ID` = ваш ID
- `OWNER_NAME` = имя получателя
- `ACCOUNT_NUMBER` = номер счета

### Шаг 5: Деплой
Render автоматически задеплоит при push в main ветку.

## Мониторинг
- Логи доступны в реальном времени
- Автоматический рестарт при ошибках
- Уведомления о статусе деплоя
