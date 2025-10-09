# 🚀 Быстрый старт PostgreSQL - 5 минут

## ✅ Что уже готово:

- [x] `database.py` обновлен (поддержка PostgreSQL + SQLite)
- [x] `requirements.txt` обновлен (psycopg2-binary добавлен)
- [x] `.env.example` обновлен
- [x] Документация создана

---

## 🎯 Что делать СЕЙЧАС (5 шагов):

### 1️⃣ Создайте PostgreSQL на Render (2 минуты)

1. Откройте: https://dashboard.render.com/
2. **New +** → **PostgreSQL**
3. Заполните:
   - Name: `qr-bot-database`
   - Database: `qr_bot_db`
   - User: `qr_bot_user`
   - Region: Frankfurt
   - Plan: **Free**
4. **Create Database**
5. Дождитесь "Available"
6. **СКОПИРУЙТЕ Internal Database URL** (начинается с `postgresql://`)

---

### 2️⃣ Обновите .env локально (30 секунд)

Откройте `.env` и добавьте:

```env
DATABASE_URL=postgresql://user:password@host/db_name
```

Замените на ваш скопированный URL.

---

### 3️⃣ Установите зависимость (30 секунд)

```bash
pip install psycopg2-binary
```

---

### 4️⃣ Протестируйте локально (30 секунд)

```bash
python database.py
```

**Должны увидеть:**
```
🐘 PostgreSQL driver loaded successfully
✅ Connected to PostgreSQL: qr_bot_db
✅ All tests passed!
```

---

### 5️⃣ Деплой на Render (1.5 минуты)

```bash
# Закоммитьте
git add .
git commit -m "Add PostgreSQL support"
git push origin main
```

**В Render Dashboard:**
1. Откройте ваш Web Service
2. **Environment** → **Add Environment Variable**
3. Key: `DATABASE_URL`
4. Value: (вставьте Internal Database URL)
5. **Save Changes**

Render автоматически задеплоит.

---

## ✅ Проверка (1 минута)

1. **Логи на Render** → должно быть:
   ```
   🐘 PostgreSQL driver loaded successfully
   ✅ Connected to PostgreSQL
   ```

2. **В боте:**
   - Отправьте `/start`
   - Создайте QR-код
   - Проверьте `/stats`

3. **Перезапустите бот** на Render
   - Manual Deploy → Deploy latest commit
   - Снова `/stats` - **данные сохранились!** 🎉

---

## 📚 Полная документация

Смотрите:
- **POSTGRESQL_SETUP.md** - подробная инструкция
- **MIGRATION_CHECKLIST.md** - пошаговый чеклист

---

## 🆘 Проблемы?

### "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### "Could not connect"
- Используйте **Internal** URL (не External)
- Проверьте база "Available" в Dashboard

### Бот использует SQLite
- Убедитесь DATABASE_URL начинается с `postgresql://`
- Проверьте Environment на Render

---

## 💡 Преимущества

✅ Данные **НЕ удаляются** при деплое  
✅ Автоматические **бэкапы** (7 дней)  
✅ **Бесплатно** навсегда (1GB)  
✅ **Production ready**  

---

**Время:** ~5 минут  
**Сложность:** Легко  
**Стоимость:** Бесплатно 🎉
