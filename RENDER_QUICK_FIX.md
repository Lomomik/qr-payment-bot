# Быстрое исправление проблемы засыпания Render

## 🚨 Проблема решена в 3 шага:

### Шаг 1: Добавьте файлы в проект

Скопируйте файл `render_keep_alive.py` в корень вашего проекта.

### Шаг 2: Обновите requirements.txt

Добавьте в `requirements.txt`:

```txt
aiohttp==3.8.5
```

### Шаг 3: Добавьте 3 строки в ваш бот

В начало файла `qr.py` добавьте импорт:

```python
# Добавьте после других импортов
from render_keep_alive import setup_render_keep_alive
```

В функции `main()` добавьте (после создания application):

```python
async def main():
    logger.info("Starting QR Payment Bot...")
    
    # 🔄 ДОБАВЬТЕ ЭТИ СТРОКИ:
    if os.getenv('RENDER'):  # Проверяем, что мы на Render
        setup_render_keep_alive()
        logger.info("✅ Render keep-alive activated")
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ... остальной код ...
```

### Шаг 4: Установите переменную окружения на Render

В настройках Render добавьте переменную:

```
RENDER_EXTERNAL_URL=https://your-app-name.onrender.com
```

(Замените `your-app-name` на реальное имя вашего приложения)

## ✅ Готово!

После деплоя ваш бот будет:
- Автоматически пинговать себя каждые 10 минут
- Иметь health endpoint на `/health`
- Никогда не засыпать

## 🔍 Проверка работы

1. Откройте `https://your-app.onrender.com/health` - должен показать `{"status": "ok"}`
2. В логах Render должны появиться сообщения: `✅ Keep-alive ping successful`

## 🆘 Если не работает

1. Проверьте, что `aiohttp` установлен в requirements.txt
2. Убедитесь, что переменная `RENDER_EXTERNAL_URL` правильная
3. Проверьте логи на наличие ошибок keep-alive

## 📱 Альтернатива: UptimeRobot

Если не хотите изменять код:

1. Зарегистрируйтесь на https://uptimerobot.com/
2. Добавьте монитор HTTP(s) для вашего Render URL
3. Установите интервал: 5 минут
4. UptimeRobot будет пинговать ваш сервис автоматически
