# 📅 Google Calendar Integration Guide

## 📋 Оглавление
1. [Обзор](#overview)
2. [Быстрый старт](#quick-start)
3. [Настройка Google Cloud](#google-cloud-setup)
4. [OAuth vs Service Account](#auth-types)
5. [Интеграция в бот](#bot-integration)
6. [Процедуры и цены](#procedures)
7. [Тестирование](#testing)

---

## 🎯 Обзор {#overview}

Модуль `google_calendar.py` позволяет боту:
- Получать сегодняшние встречи из Google Calendar
- Автоматически определять процедуру и цену из названия события
- Создавать кнопки быстрой оплаты для запланированных услуг

**Статус:** Модуль готов, но не интегрирован в production бот (`qr.py`)

---

## 🚀 Быстрый старт {#quick-start}

### 1. Установка зависимостей

Уже включены в `requirements.txt`:
```
google-auth==2.23.3
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.103.0
```

### 2. Настройка переменных окружения

Добавьте в `.env.test`:
```env
# Для локального тестирования (OAuth)
GOOGLE_CALENDAR_TYPE=oauth
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_ID=primary

# Для сервера (Service Account)
# GOOGLE_CALENDAR_TYPE=service_account
# GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
# GOOGLE_CALENDAR_ID=your-email@gmail.com
```

### 3. Тестирование

```bash
# Запустите тестовый модуль
python google_calendar.py

# Или используйте mock-данные
python -c "from google_calendar import get_mock_today_events, parse_events_for_payment; \
           events = get_mock_today_events(); \
           print(parse_events_for_payment(events))"
```

---

## ☁️ Настройка Google Cloud {#google-cloud-setup}

### Шаг 1: Создание проекта

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект: "QR Payment Bot"
3. Включите Google Calendar API:
   - APIs & Services → Library
   - Найдите "Google Calendar API"
   - Нажмите "Enable"

### Шаг 2: OAuth Credentials (для локального тестирования)

1. **OAuth Consent Screen:**
   - APIs & Services → OAuth consent screen
   - Выберите "External"
   - Заполните:
     - App name: "QR Payment Bot"
     - User support email: ваш email
     - Developer contact: ваш email
   - Добавьте scope: `https://www.googleapis.com/auth/calendar.readonly`
   - Добавьте test users (ваш email)

2. **Создание OAuth Client ID:**
   - APIs & Services → Credentials
   - Create Credentials → OAuth 2.0 Client IDs
   - Application type: "Desktop application"
   - Name: "QR Bot Local"
   - Скачайте JSON → переименуйте в `credentials.json`
   - Поместите в корень проекта

3. **Первая авторизация:**
   ```bash
   python google_calendar.py
   # Откроется браузер для авторизации
   # Разрешите доступ к календарю
   # Токен сохранится в token.pickle
   ```

### Шаг 3: Service Account (для production)

1. **Создание Service Account:**
   - APIs & Services → Credentials
   - Create Credentials → Service Account
   - Name: "qr-bot-calendar-reader"
   - Role: Viewer
   - Нажмите "Done"

2. **Создание ключа:**
   - Кликните на созданный Service Account
   - Keys → Add Key → Create new key
   - Type: JSON
   - Скачайте → переименуйте в `service-account.json`
   - Поместите в корень проекта

3. **Предоставление доступа к календарю:**
   - Откройте Google Calendar
   - Settings → ваш календарь → Share with specific people
   - Добавьте email Service Account (из JSON файла)
   - Права: "See all event details"

4. **Настройка .env:**
   ```env
   GOOGLE_CALENDAR_TYPE=service_account
   GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
   GOOGLE_CALENDAR_ID=your-email@gmail.com
   ```

---

## 🔐 OAuth vs Service Account {#auth-types}

### OAuth (рекомендуется для локального тестирования)

**Плюсы:**
- ✅ Простая настройка
- ✅ Доступ к личному календарю
- ✅ Не требует дополнительных прав

**Минусы:**
- ❌ Требует браузер для первой авторизации
- ❌ Токен истекает (обновляется автоматически)
- ❌ Не подходит для серверов без GUI

**Использование:**
```python
from google_calendar import GoogleCalendarService

service = GoogleCalendarService()
service.auth_type = 'oauth'
service.authenticate()  # Откроется браузер
events = service.get_today_events()
```

### Service Account (рекомендуется для production)

**Плюсы:**
- ✅ Работает без браузера
- ✅ Подходит для серверов
- ✅ Долгосрочный доступ

**Минусы:**
- ❌ Требует явного предоставления доступа к календарю
- ❌ Немного сложнее настройка

**Использование:**
```python
from google_calendar import GoogleCalendarService

service = GoogleCalendarService()
service.auth_type = 'service_account'
service.authenticate()
events = service.get_today_events()
```

---

## 🤖 Интеграция в бот {#bot-integration}

### Пример добавления в qr.py

```python
# В начале файла
from google_calendar import calendar_service, parse_events_for_payment

async def calendar_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает сегодняшние встречи для быстрой оплаты"""
    
    # Получаем события
    events = calendar_service.get_today_events()
    
    if not events:
        await update.message.reply_text(
            '📅 На сегодня нет запланированных встреч',
            reply_markup=get_main_keyboard()
        )
        return
    
    # Парсим события для оплаты
    payment_options = parse_events_for_payment(events)
    
    if not payment_options:
        await update.message.reply_text(
            '📅 Встречи найдены, но не удалось определить цены.\n'
            'Используйте ручной ввод /payment',
            reply_markup=get_main_keyboard()
        )
        return
    
    # Создаем кнопки
    keyboard = []
    for option in payment_options:
        keyboard.append([
            InlineKeyboardButton(
                option['display_text'],
                callback_data=f"calendar_pay_{option['price']}"
            )
        ])
    
    await update.message.reply_text(
        '📅 Сегодняшние встречи:\n\n'
        'Выберите встречу для создания QR-кода:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# В main():
application.add_handler(CommandHandler("calendar", calendar_payment_command))
```

---

## 💰 Процедуры и цены {#procedures}

### Словарь цен (40+ процедур)

```python
PROCEDURE_PRICES = {
    # Брови
    'úprava obočí': 800,
    'úprava a barvení obočí': 1000,
    'zesvětlení obočí': 1200,
    'laminace obočí': 1400,
    
    # Ресницы
    'laminace řas': 1500,
    'barvení řas': 500,
    'botox řas': 1600,
    
    # Комбо
    'laminace řas + úprava obočí': 2000,
    'laminace obočí a řas': 2500,
    
    # Макияж
    'líčení': 1200,
    'svatební líčení': 2500,
    
    # ... (см. google_calendar.py)
}
```

### Умное определение процедуры

Бот распознает процедуру по ключевым словам в названии события:

**Примеры:**
- `"Laminace řas - Anna"` → `laminace řas` → 1500 CZK
- `"Úprava obočí Marie"` → `úprava obočí` → 800 CZK
- `"Líčení svatební - Petra"` → `svatební líčení` → 2500 CZK

### Добавление новых процедур

Отредактируйте `google_calendar.py`:
```python
PROCEDURE_PRICES = {
    # ... существующие ...
    'новая процедура': цена_czk,
}

# Опционально: добавьте алиас
PROCEDURE_ALIASES = {
    'короткое название': 'новая процедура',
}
```

---

## 🧪 Тестирование {#testing}

### Mock-данные

Модуль включает тестовые данные для разработки без Google API:

```python
from google_calendar import get_mock_today_events, parse_events_for_payment

# Получить тестовые события
events = get_mock_today_events()
print(f"Найдено {len(events)} событий")

# Парсить для оплаты
options = parse_events_for_payment(events)
for option in options:
    print(f"  {option['display_text']}")
```

**Тестовые события:**
- Laminace řas + úprava obočí - Anna (09:00) → 2000 CZK
- Zesvětlení s úpravou a tonováním - Marie (11:00) → 1600 CZK
- Líčení & účes - Petra (14:00) → 2000 CZK
- Konzultace + návrh - Elena (16:30) → 800 CZK

### Тестирование с реальным API

```bash
# 1. Настройте credentials (см. выше)

# 2. Запустите модуль
python google_calendar.py

# 3. Проверьте вывод
# Должны увидеть:
# - Найденные события
# - Определенные процедуры
# - Цены
```

### Проверка формата названий

```python
from google_calendar import extract_procedure_from_title, get_procedure_price

test_titles = [
    "Laminace řas - клиент",
    "Úprava a barvení - Anna",
    "Встреча консультация"
]

for title in test_titles:
    procedure = extract_procedure_from_title(title)
    price = get_procedure_price(procedure) if procedure else None
    print(f"{title} → {procedure} → {price} CZK")
```

---

## 🔒 Безопасность

**Никогда не коммитьте:**
```
credentials.json          # OAuth credentials
token.pickle             # OAuth token
service-account.json     # Service Account key
```

**Добавлено в .gitignore:**
```gitignore
credentials.json
token.pickle
service-account.json
*.json  # На всякий случай
```

---

## 🐛 Troubleshooting

### "Service Account email not found"
→ Предоставьте доступ к календарю для email из `service-account.json`

### "Calendar ID not found"
→ Проверьте `GOOGLE_CALENDAR_ID` в `.env`
→ Используйте `primary` для основного календаря или email владельца

### "No module named 'google'"
→ Установите зависимости: `pip install -r requirements.txt`

### "Browser required but not available"
→ Используйте Service Account вместо OAuth для серверов

---

## 📝 Заметки

1. **Формат названий событий** - включайте название процедуры на чешском для автоопределения
2. **Timezone** - модуль использует системный timezone
3. **Performance** - Calendar API имеет лимиты (10,000 запросов/день)
4. **Альтернатива** - можно использовать Fresha API напрямую

---

**Версия:** 1.0  
**Модуль:** `google_calendar.py`  
**Статус:** Готов к использованию, требует активации в боте
