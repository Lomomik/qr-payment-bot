# QR Payment Bot - Google Calendar Integration

## 🚀 Быстрый старт с Google Calendar

### Вариант 1: Мгновенный тест (мок-данные)
```bash
python qr_test.py
```
Бот запустится с тестовыми календарными событиями.

### Вариант 2: Реальный Google Calendar
1. **Следуйте инструкциям:** `REAL_GOOGLE_CALENDAR_SETUP.md`
2. **Тест подключения:**
   ```bash
   python test_calendar.py
   ```
3. **Запуск бота:**
   ```bash
   python qr_test.py
   ```

## 📋 Проверка готовности

### Файлы для Google Calendar API:
- `✅ google_calendar.py` - модуль интеграции
- `❓ credentials.json` - OAuth credentials (см. REAL_GOOGLE_CALENDAR_SETUP.md)
- `❓ token.json` - авто-создается при первом запуске

### Переменные окружения (.env.test):
```env
BOT_TOKEN=your_test_bot_token
ADMIN_TELEGRAM_ID=your_telegram_id
OWNER_NAME=ULIANA EMELINA (TEST)
ACCOUNT_NUMBER=3247217010/3030
```

## 🧪 Тестирование

### 1. Проверка Calendar API:
```bash
python test_calendar.py
```

### 2. Запуск тестового бота:
```bash
python qr_test.py
```

### 3. В Telegram боте:
1. `/start`
2. `💰 Создать QR-код для оплаты`
3. Выберите событие из календаря
4. Получите QR-код с чешской банковской информацией

## 🔧 Функционал

### Google Calendar Integration:
- ✅ Автоматическое получение событий на сегодня
- ✅ Определение процедур по названию события
- ✅ Автоматический расчет цен
- ✅ Fallback на мок-данные при ошибках API

### Поддерживаемые процедуры:
- 🌿 **Брови:** Úprava, Barvení, Zesvětlení, Laminace
- 👁️ **Ресницы:** Laminace řas, Barvení řas
- ✨ **Комбо:** Laminace řas + úprava obočí
- 👄 **Красота:** Líčení, Účes
- 💬 **Консультации:** Konzultace

### Автоматические цены:
- Úprava obočí: 800 CZK
- Laminace řas: 1500 CZK
- Líčení: 1200 CZK
- И другие...

## 🆘 Проблемы и решения

### "Google Calendar не подключен"
1. Запустите: `python test_calendar.py`
2. Проверьте `credentials.json`
3. Следуйте `REAL_GOOGLE_CALENDAR_SETUP.md`

### "No events found"
1. Создайте тестовые события в Google Calendar
2. События должны содержать названия процедур (например: "Úprava obočí - Клиент")

### "Invalid credentials"
1. Пересоздайте `credentials.json` в Google Cloud Console
2. Добавьте ваш email в test users
3. Удалите `token.json` и попробуйте снова

## 📁 Структура проекта

```
QR platba - telegram/
├── qr_test.py                      # Тестовый бот с календарем
├── google_calendar.py              # Google Calendar API модуль
├── test_calendar.py                # Тест календарного подключения
├── REAL_GOOGLE_CALENDAR_SETUP.md   # Подробная настройка API
├── credentials.json                # OAuth credentials (создать)
├── token.json                      # Auto-generated token
├── .env.test                       # Тестовые переменные
└── requirements.txt                # Python dependencies
```

## 🔄 Развертывание

### Локальное тестирование:
```bash
# Установка зависимостей
pip install -r requirements.txt

# Тест Calendar API
python test_calendar.py

# Запуск тестового бота
python qr_test.py
```

### Production готовность:
- ✅ Реальные события из Google Calendar
- ✅ Чешский банковский QR формат (SPD)
- ✅ Автоматическое определение цен
- ✅ Fallback на мок-данные
- ✅ Подробное логирование

## 🎯 Следующие шаги

1. **Настройте Google Calendar API** (REAL_GOOGLE_CALENDAR_SETUP.md)
2. **Протестируйте с реальными событиями**
3. **Адаптируйте процедуры под ваш салон**
4. **Переходите на production bot** (qr.py)
