# 🐘 PostgreSQL на Render - Пошаговая инструкция

## 🎯 Зачем PostgreSQL?

- ✅ **Персистентное хранилище** - данные НЕ удаляются при деплое
- ✅ **Бесплатно** - Render предоставляет PostgreSQL бесплатно
- ✅ **До 1GB данных** - достаточно для тысяч транзакций
- ✅ **Профессиональная БД** - лучше SQLite для production

---

## 📋 Шаг 1: Создание PostgreSQL базы на Render

### 1.1 Откройте Render Dashboard

Перейдите: https://dashboard.render.com/

### 1.2 Создайте новую PostgreSQL базу

1. Нажмите **"New +"** (правый верхний угол)
2. Выберите **"PostgreSQL"**

### 1.3 Настройте параметры

Заполните форму:

```
Name: qr-bot-database
Database: qr_bot_db
User: qr_bot_user
Region: Frankfurt (или ближайший к вашему боту)
PostgreSQL Version: 16 (latest)
Plan: Free
```

**Важно:** Запомните/запишите эти данные!

### 1.4 Создайте базу

1. Нажмите **"Create Database"**
2. Подождите 1-2 минуты пока база создается
3. Статус изменится на **"Available"**

### 1.5 Получите Connection String

После создания вы увидите страницу с деталями базы:

1. Найдите раздел **"Connections"**
2. Скопируйте **"Internal Database URL"** (важно! не External)
   
   Формат:
   ```
   postgresql://qr_bot_user:пароль@dpg-xxxxx/qr_bot_db
   ```

3. **СОХРАНИТЕ ЭТУ СТРОКУ!** Она понадобится для .env

---

## 📋 Шаг 2: Обновление кода бота

### 2.1 Обновите .env файл

Добавьте в `.env`:

```env
# Существующие переменные
BOT_TOKEN=your_bot_token
ADMIN_TELEGRAM_ID=your_admin_id
OWNER_NAME=ULIANA EMELINA
ACCOUNT_NUMBER=3247217010/3030
IBAN=CZ3230300000003247217010

# НОВАЯ переменная для PostgreSQL
DATABASE_URL=postgresql://qr_bot_user:пароль@dpg-xxxxx/qr_bot_db
```

### 2.2 Обновите переменные окружения на Render

1. Откройте ваш Web Service в Dashboard
2. Перейдите **Environment** (левое меню)
3. Нажмите **"Add Environment Variable"**
4. Добавьте:
   - **Key:** `DATABASE_URL`
   - **Value:** (вставьте Internal Database URL из шага 1.5)
5. Нажмите **"Save Changes"**

---

## 📋 Шаг 3: Установка зависимостей

### 3.1 Обновлен requirements.txt

Уже добавлено:
```
psycopg2-binary==2.9.9
```

### 3.2 Локальное тестирование

Если хотите тестировать локально:

```bash
# Установите PostgreSQL локально (опционально)
# macOS:
brew install postgresql@16

# Ubuntu/Debian:
sudo apt-get install postgresql

# Windows:
# Скачайте с https://www.postgresql.org/download/

# Установите Python пакет
pip install psycopg2-binary
```

---

## 📋 Шаг 4: Проверка работы

### 4.1 Локальный тест

```bash
# Запустите database.py для проверки подключения
python database.py
```

**Ожидаемый вывод:**
```
✅ Connected to PostgreSQL: qr_bot_db
Database initialized successfully
🧪 Testing database module...
✅ User added
✅ Transaction added
✅ User stats: {...}
✅ All tests passed!
```

### 4.2 Деплой на Render

```bash
git add .
git commit -m "Add PostgreSQL support for persistent storage"
git push origin main
```

### 4.3 Проверьте логи на Render

В Dashboard → Logs смотрите:
```
✅ Connected to PostgreSQL: qr_bot_db
✅ Database module loaded successfully
Database initialized successfully
```

---

## 📊 Управление базой данных

### Просмотр данных через Render Dashboard

1. Откройте вашу PostgreSQL базу в Dashboard
2. Перейдите на вкладку **"Shell"**
3. Выполните SQL запросы:

```sql
-- Посмотреть все таблицы
\dt

-- Посмотреть пользователей
SELECT * FROM users ORDER BY last_seen DESC LIMIT 10;

-- Посмотреть транзакции
SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 20;

-- Общая статистика
SELECT 
    COUNT(*) as total_users,
    (SELECT COUNT(*) FROM transactions) as total_transactions,
    (SELECT SUM(amount) FROM transactions) as total_amount
FROM users;

-- Популярные услуги
SELECT service, COUNT(*) as count 
FROM transactions 
WHERE service IS NOT NULL 
GROUP BY service 
ORDER BY count DESC 
LIMIT 10;

-- Выйти
\q
```

### Подключение через pgAdmin (опционально)

1. Скачайте pgAdmin: https://www.pgadmin.org/
2. Создайте новое подключение:
   - Host: (из External Database URL)
   - Port: 5432
   - Database: qr_bot_db
   - Username: qr_bot_user
   - Password: (ваш пароль из connection string)

---

## 🔐 Безопасность

### ✅ Что уже защищено:

1. **DATABASE_URL в .env** - не коммитится в Git
2. **Internal URL** - доступен только внутри Render
3. **SSL подключение** - автоматически используется

### ⚠️ Важно:

1. **НИКОГДА не коммитьте DATABASE_URL** в Git
2. Добавлено в `.gitignore`:
   ```
   .env
   .env.test
   .env.local
   ```

---

## 🔄 Миграция данных

### Если у вас уже есть SQLite данные:

```bash
# Экспортируйте из SQLite
sqlite3 bot_stats.db .dump > backup.sql

# Импортируйте в PostgreSQL (через Render Shell)
# 1. Откройте PostgreSQL Shell в Render Dashboard
# 2. Скопируйте содержимое backup.sql
# 3. Вставьте в Shell

# Или используйте pgLoader (автоматически)
brew install pgloader  # macOS
pgloader bot_stats.db postgresql://...
```

**Примечание:** Обычно миграция не нужна - просто начните с чистой базы.

---

## 🆘 Troubleshooting

### "Could not connect to server"

1. Проверьте DATABASE_URL в Environment переменных
2. Убедитесь что используете **Internal** URL (не External)
3. Проверьте что PostgreSQL база "Available" в Dashboard

### "psycopg2 not installed"

```bash
pip install psycopg2-binary
# или
pip install -r requirements.txt
```

### "SSL connection required"

Добавьте `?sslmode=require` в конец DATABASE_URL:
```
postgresql://user:pass@host/db?sslmode=require
```

### "Too many connections"

Free план имеет лимит: **97 подключений**.

Решение в коде уже реализовано - используем connection pooling.

---

## 📊 Лимиты Free плана

| Параметр | Лимит |
|----------|-------|
| Хранилище | 1 GB |
| RAM | 256 MB |
| Подключения | 97 одновременных |
| Бэкапы | 7 дней истории |
| Bandwidth | Безлимитно |

**Для бота этого более чем достаточно!**

---

## 🎯 Upgrade опции (если понадобится)

### Starter Plan ($7/месяц):
- 10 GB хранилища
- 1 GB RAM
- Более быстрая производительность

### Когда нужен Upgrade:
- Более 1 GB данных (≈100,000+ транзакций)
- Нужно больше подключений
- Нужны ежечасные бэкапы

---

## ✅ Преимущества PostgreSQL vs SQLite

| Параметр | SQLite | PostgreSQL |
|----------|--------|------------|
| **Персистентность на Render Free** | ❌ Удаляется | ✅ Сохраняется |
| **Concurrent writes** | ⚠️ Ограничено | ✅ Отлично |
| **Размер БД** | До 2GB | 1GB (Free), 10GB+ (Paid) |
| **Бэкапы** | ❌ Ручные | ✅ Автоматические (7 дней) |
| **Production ready** | ⚠️ Для малых нагрузок | ✅ Да |

---

## 🚀 Следующие шаги

После настройки PostgreSQL:

1. ✅ Протестируйте локально: `python database.py`
2. ✅ Задеплойте на Render: `git push`
3. ✅ Проверьте логи: Dashboard → Logs
4. ✅ Создайте первый QR-код для проверки
5. ✅ Выполните `/stats` чтобы увидеть данные
6. ✅ Перезапустите бот - данные останутся! 🎉

---

## 📝 Контрольный чеклист

- [ ] PostgreSQL база создана на Render
- [ ] DATABASE_URL получен и сохранен
- [ ] DATABASE_URL добавлен в .env локально
- [ ] DATABASE_URL добавлен в Environment на Render
- [ ] psycopg2-binary в requirements.txt
- [ ] database.py обновлен для PostgreSQL
- [ ] Код протестирован локально
- [ ] Код задеплоен на Render
- [ ] Логи проверены - подключение успешно
- [ ] Первая транзакция создана
- [ ] Данные сохраняются после перезапуска

---

**Версия:** 1.0  
**Дата:** 9 октября 2024  
**Статус:** ✅ Production Ready

🎉 **Поздравляем! Теперь ваши данные будут сохраняться навсегда!**
