# 💾 База данных и аналитика - Инструкция

## 📋 Обзор

Бот теперь использует **SQLite** для хранения:
- 👥 Информация о пользователях
- 💰 История всех транзакций (QR-кодов)
- 📊 События и действия пользователей

**Преимущества:**
- ✅ Данные сохраняются при перезапуске
- ✅ Расширенная аналитика и отчеты
- ✅ Отслеживание популярных услуг
- ✅ История по дням

---

## 🚀 Быстрый старт

### Автоматическая инициализация

База данных создается **автоматически** при первом запуске бота:

```bash
python qr.py
```

Вы увидите в логах:
```
✅ Database module loaded successfully
Database initialized at bot_stats.db
```

---

## 📊 Структура базы данных

### Таблица `users`
Хранит информацию о пользователях:
- `user_id` - Telegram ID (первичный ключ)
- `username` - Username
- `first_name`, `last_name` - Имя и фамилия
- `first_seen`, `last_seen` - Даты первого и последнего визита
- `total_requests` - Общее количество запросов
- `is_admin` - Флаг администратора

### Таблица `transactions`
Хранит все транзакции (созданные QR-коды):
- `id` - Уникальный ID транзакции
- `user_id` - ID пользователя
- `amount` - Сумма в CZK
- `service` - Название услуги (может быть NULL)
- `timestamp` - Дата и время

### Таблица `events`
Хранит события (действия пользователей):
- `id` - Уникальный ID
- `user_id` - ID пользователя
- `event_type` - Тип события (start, payment_start, qr_generated)
- `event_data` - Дополнительные данные
- `timestamp` - Дата и время

---

## 📱 Команды бота с БД

### `/stats` - Базовая статистика (админ)

Показывает:
- 👥 Всего пользователей
- 💰 Всего транзакций
- 💵 Общую сумму
- 📊 Среднюю сумму
- 🟢 Активных за 24 часа
- **Топ-5 пользователей** с количеством QR и суммами
- **Топ-5 популярных услуг**

**Пример вывода:**
```
📊 СТАТИСТИКА БОТА (БД)

👥 Всего пользователей: 15
💰 Всего транзакций: 47
💵 Общая сумма: 68,500 CZK
📊 Средняя сумма: 1,457 CZK
🟢 Активных за 24ч: 5

Топ пользователей:
1. @username1: 12 QR, 18,000 CZK
2. @username2: 8 QR, 12,400 CZK
3. @username3: 6 QR, 9,000 CZK
4. @username4: 5 QR, 7,500 CZK
5. @username5: 4 QR, 6,000 CZK

Популярные услуги:
1. LAMINACE RAS: 15x
2. ÚPRAVA A BARVENÍ: 12x
3. LAMINACE RAS + ÚPRAVA: 8x
4. ZESVĚTLENÍ: 6x
5. LÍČENÍ & ÚČES: 4x
```

---

## 🔧 Управление базой данных

### Расположение файла

- **По умолчанию:** `bot_stats.db` (в корне проекта)
- **Настройка:** переменная окружения `DATABASE_PATH`

```env
# В .env:
DATABASE_PATH=/path/to/custom/database.db
```

### Резервное копирование

```bash
# Создать backup
cp bot_stats.db bot_stats_backup_$(date +%Y%m%d).db

# Восстановить из backup
cp bot_stats_backup_20241009.db bot_stats.db
```

### Просмотр БД (SQLite Browser)

Используйте **DB Browser for SQLite** (бесплатно):
- Download: https://sqlitebrowser.org/
- Open: `bot_stats.db`
- Browse Data → выберите таблицу

### SQL запросы

```bash
# Запустить SQLite CLI
sqlite3 bot_stats.db

# Примеры запросов:
sqlite> SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 10;
sqlite> SELECT service, COUNT(*) FROM transactions GROUP BY service;
sqlite> SELECT SUM(amount) FROM transactions WHERE date(timestamp) = date('now');
sqlite> .exit
```

---

## 📈 Расширенная аналитика

### Модуль `analytics.py`

Предоставляет дополнительные отчеты:

```python
from analytics import (
    format_daily_report,      # Дневной отчет за 7 дней
    format_services_report,   # Детальный отчет по услугам
    format_users_report,      # Детальный отчет по пользователям
    format_summary_report     # Общий отчет с последними транзакциями
)

# Получить отчет
print(format_daily_report())
```

### Запуск вручную

```bash
python analytics.py
```

**Вывод:**
- Общая аналитика
- Дневная статистика за 7 дней
- Популярные услуги с процентами
- Активные пользователи (топ-10)

---

## 🔍 Отладка и мониторинг

### Проверка работы БД

```python
# Запустите database.py напрямую для тестирования
python database.py
```

**Ожидаемый вывод:**
```
🧪 Testing database module...
✅ User added
✅ Transaction added
✅ User stats: {...}
✅ Total stats: {...}
✅ All tests passed!
```

### Логи

Бот логирует все действия с БД:
```
✅ Database module loaded successfully
Transaction added: user=123456, amount=1500.0, service=LAMINACE RAS
Database error: ... (если что-то пошло не так)
```

### Fallback режим

Если БД недоступна, бот автоматически использует **in-memory статистику**:
```
⚠️ Database module not found, using in-memory stats
📊 СТАТИСТИКА БОТА (память)  # вместо (БД)
```

---

## 🚨 Troubleshooting

### "Database is locked"
```bash
# Закройте все подключения к БД
# Проверьте нет ли других экземпляров бота
ps aux | grep qr.py
kill <PID>
```

### "No module named database"
```bash
# Убедитесь что database.py в той же директории что и qr.py
ls -la database.py
```

### БД не создается
```bash
# Проверьте права на запись
chmod 755 .
# Проверьте место на диске
df -h
```

### Миграция старых данных

Если у вас была старая версия без БД:
```python
# Старая статистика в памяти не переносится автоматически
# Но новые данные сохраняются в БД с первого запроса
```

---

## 🔐 Безопасность

### Добавьте в .gitignore

Уже добавлено:
```
bot_stats.db
bot_stats.db-journal
*.db
*.db-journal
```

### На Render

База данных будет **сбрасываться при каждом деплое** на Render Free Plan.

**Решения:**
1. **Render Paid Plan** - персистентный диск
2. **Внешняя БД** - PostgreSQL (Render поддерживает)
3. **Экспорт в Google Sheets** - периодический backup

---

## 📝 API Reference

### Database класс

```python
from database import db

# Добавить/обновить пользователя
db.add_or_update_user(user_id, username, first_name, last_name, is_admin)

# Добавить транзакцию
db.add_transaction(user_id, amount, service)

# Добавить событие
db.add_event(user_id, event_type, event_data)

# Получить статистику пользователя
stats = db.get_user_stats(user_id)

# Получить всех пользователей
users = db.get_all_users_stats()

# Общая статистика
total = db.get_total_stats()

# Последние транзакции
recent = db.get_recent_transactions(limit=10)

# Популярные услуги
services = db.get_popular_services(limit=10)

# Дневная статистика
daily = db.get_daily_stats(days=7)
```

---

## 🎯 Будущие улучшения

- [ ] Экспорт в CSV/Excel
- [ ] Графики и визуализация
- [ ] Email отчеты
- [ ] Интеграция с Google Sheets
- [ ] PostgreSQL для production
- [ ] Webhook для real-time обновлений

---

**Версия:** 1.0  
**Дата:** 9 октября 2024  
**Статус:** ✅ Production Ready
