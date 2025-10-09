# ✅ Чеклист миграции на PostgreSQL

## 📋 Шаг за шагом

### 1. Создание PostgreSQL базы на Render ✅

- [ ] Зайти на https://dashboard.render.com/
- [ ] New → PostgreSQL
- [ ] Заполнить форму:
  - Name: `qr-bot-database`
  - Database: `qr_bot_db`  
  - User: `qr_bot_user`
  - Region: Frankfurt
  - Plan: Free
- [ ] Нажать "Create Database"
- [ ] Дождаться статуса "Available"
- [ ] Скопировать **Internal Database URL**

---

### 2. Обновление локального окружения ✅

- [x] Файл `database.py` обновлен (поддержка PostgreSQL)
- [x] `requirements.txt` обновлен (`psycopg2-binary` добавлен)
- [x] `.env.example` обновлен (добавлен `DATABASE_URL`)

**Теперь обновите ваш `.env`:**

```bash
# Откройте .env и добавьте:
DATABASE_URL=postgresql://user:password@host/db_name
```

Замените на ваш Internal Database URL из Render.

---

### 3. Установка зависимостей

```bash
# Установите psycopg2-binary
pip install psycopg2-binary

# Или установите все зависимости
pip install -r requirements.txt
```

---

### 4. Локальное тестирование

```bash
# Проверьте что БД работает
python database.py
```

**Ожидаемый вывод:**
```
🐘 PostgreSQL driver loaded successfully
📊 Database type: postgresql
✅ Connected to PostgreSQL: qr_bot_db
Database initialized successfully
🧪 Testing database module...
✅ User added
✅ Transaction added
✅ User stats: {...}
✅ All tests passed!
```

---

### 5. Обновление переменных на Render

- [ ] Открыть Render Dashboard
- [ ] Выбрать ваш Web Service (qr-payment-bot)
- [ ] Перейти в **Environment** (левое меню)
- [ ] Нажать **"Add Environment Variable"**
- [ ] Добавить:
  - Key: `DATABASE_URL`
  - Value: (Internal Database URL из шага 1)
- [ ] Нажать **"Save Changes"**

---

### 6. Деплой обновлений

```bash
# Закоммитьте изменения
git add .
git commit -m "Add PostgreSQL support for persistent storage

- Replace SQLite with PostgreSQL
- Add psycopg2-binary dependency
- Universal database module supporting both SQLite and PostgreSQL
- Update .env.example with DATABASE_URL
- Add PostgreSQL setup guide

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

# Задеплойте
git push origin main
```

---

### 7. Проверка на Render

**Следите за логами в Render Dashboard:**

- [ ] Открыть Render Dashboard → ваш сервис → Logs
- [ ] Дождаться деплоя
- [ ] Проверить логи:

**Должны увидеть:**
```
🐘 PostgreSQL driver loaded successfully
📊 Database type: postgresql
✅ Connected to PostgreSQL: qr_bot_db
✅ Database module loaded successfully
Database initialized successfully
🤖 Bot is running...
```

---

### 8. Проверка работы бота

- [ ] Отправить `/start` боту
- [ ] Создать QR-код через `/payment`
- [ ] Отправить `/stats` (для админа)

**Должны увидеть:**
```
📊 СТАТИСТИКА БОТА (БД)
👥 Всего пользователей: 1
💰 Всего транзакций: 1
...
```

---

### 9. Проверка персистентности

**КРИТИЧЕСКИ ВАЖНЫЙ ТЕСТ:**

1. [ ] Создайте несколько QR-кодов
2. [ ] Проверьте `/stats` - запомните числа
3. [ ] Перезапустите бот на Render:
   - Dashboard → Manual Deploy → Deploy latest commit
4. [ ] Дождитесь перезапуска
5. [ ] Снова проверьте `/stats`

**Результат:** Данные должны сохраниться! 🎉

---

### 10. Просмотр данных в PostgreSQL

**Через Render Shell:**

- [ ] Dashboard → PostgreSQL база → Shell
- [ ] Выполните команды:

```sql
-- Посмотреть все таблицы
\dt

-- Посмотреть пользователей
SELECT * FROM users;

-- Посмотреть транзакции
SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 10;

-- Общая статистика
SELECT 
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM transactions) as transactions,
    (SELECT SUM(amount) FROM transactions) as total_amount;

-- Выйти
\q
```

---

## 🎯 Финальная проверка

### Все работает если:

✅ Логи показывают "Connected to PostgreSQL"  
✅ Бот отвечает на команды  
✅ `/stats` показывает данные из БД  
✅ После перезапуска данные сохраняются  
✅ Транзакции записываются в PostgreSQL  

---

## 🆘 Если что-то пошло не так

### "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### "Could not connect to PostgreSQL"
1. Проверьте DATABASE_URL в Environment
2. Убедитесь что используете Internal URL (не External)
3. Проверьте что PostgreSQL база "Available"

### "SSL connection required"
Уже исправлено в коде: `'sslmode': 'require'`

### Бот работает но использует SQLite
1. Проверьте DATABASE_URL начинается с `postgresql://`
2. Проверьте логи: должно быть "Database type: postgresql"
3. Перезапустите с правильным DATABASE_URL

### Хочу вернуться на SQLite
```bash
# Просто удалите DATABASE_URL из .env и Render Environment
# Бот автоматически вернется к SQLite
```

---

## 📊 Сравнение до/после

| Параметр | До (SQLite) | После (PostgreSQL) |
|----------|-------------|-------------------|
| Персистентность | ❌ Удаляется | ✅ Сохраняется |
| Данные после деплоя | ❌ Потеряны | ✅ Сохранены |
| Backup | ❌ Ручной | ✅ Автоматический (7 дней) |
| Размер | до 2GB | до 1GB (Free) |
| Подходит для production | ⚠️ Условно | ✅ Да |

---

## 🎉 Поздравляем!

Теперь ваш бот использует **профессиональную базу данных** и все данные сохраняются навсегда!

**Полезные ссылки:**
- Render Dashboard: https://dashboard.render.com/
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Render PostgreSQL Guide: https://render.com/docs/databases

---

**Дата миграции:** _____________  
**Выполнено:** ☐ Да ☐ Нет  
**Проблемы:** _____________
