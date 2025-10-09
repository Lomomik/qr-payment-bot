# 💄 QR Payment Bot для салона красоты

Telegram бот для быстрого создания QR-кодов для оплаты услуг салона красоты в Чехии.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-21.4-blue.svg)](https://python-telegram-bot.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Содержание
- [Для кого этот бот](#для-кого-этот-бот)
- [Функциональность](#функциональность)
- [Быстрый старт](#быстрый-старт)
- [Команды бота](#команды-бота)
- [Развертывание](#развертывание)
- [Тестирование](#тестирование)
- [Документация](#документация)

---

## 👥 Для кого этот бот?

Создан специально для **сотрудников салона красоты Noéme** для упрощения процесса оплаты услуг клиентами.

### ✅ Работает с банками:
- **Air Bank** ✅
- **Raiffeisenbank CZ** ✅
- Другие чешские банки с поддержкой SPD формата

---

## 🚀 Функциональность

### Основные возможности:
- 💰 **Быстрое создание QR-кодов** - выбор суммы одним нажатием (500-1800 CZK)
- 🌿 **Умный выбор услуг** - динамическая фильтрация по сумме
- ✏️ **Кастомные услуги** - возможность ввода своей услуги
- 📱 **Простой интерфейс** - кнопки для всех действий
- 🔐 **Безопасность** - никакие данные не сохраняются
- 📊 **Статистика** - отслеживание использования (только для админа)

### Умная фильтрация услуг:
- **≤1000 CZK:** Базовые услуги (úprava, barvení, laminace řas)
- **>1000 CZK:** Комбинированные услуги (laminace + úprava, líčení & účes)

### Поддерживаемые услуги (13):
- 🌿 Úprava, úprava a barvení, zesvětlení, laminace obočí
- 👁️ Laminace řas, barvení řas
- ✨ Комбинированные процедуры
- 👄 Líčení, účes, líčení & účes
- 🌿 Depilace obličeje

---

## ⚡ Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <ваш-репозиторий>
cd "QR platba - telegram"
```

### 2. Установка зависимостей

```bash
# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` (скопируйте из `.env.example`):

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=your_telegram_id_here

# Payment Configuration
OWNER_NAME=ULIANA EMELINA
ACCOUNT_NUMBER=3247217010/3030
IBAN=CZ3230300000003247217010

# Render (опционально)
RENDER_EXTERNAL_URL=https://your-app.onrender.com
```

### 4. Запуск бота

```bash
# Production версия
python qr.py

# Тестовая версия (использует .env.test)
python qr_test.py
```

---

## 📱 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота и главное меню |
| `/payment` | Создать QR-код для оплаты |
| `/help` | Инструкция для сотрудника |
| `/info` | Реквизиты счета салона |
| `/stats` | Статистика использования (только админ) |

---

## 🌍 Развертывание

### Render.com (рекомендуется)

1. **Push в GitHub:**
   ```bash
   git add .
   git commit -m "Deploy"
   git push
   ```

2. **Создайте Web Service на Render:**
   - Runtime: Python 3
   - Build: `pip install --upgrade pip && pip install -r requirements.txt`
   - Start: `python qr.py`

3. **Добавьте переменные окружения** (см. выше)

📖 **Подробная инструкция:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Другие платформы:
- Oracle Cloud Always Free
- Railway
- Fly.io

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# Конкретный файл
pytest tests/test_qr_generation.py

# С покрытием кода
pytest --cov=. --cov-report=html
```

### Тестовый бот

```bash
# Создайте .env.test с тестовым токеном
python qr_test.py
```

---

## 📚 Документация

### Основная документация:
- **[README.md](README.md)** - этот файл (обзор проекта)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - полное руководство по развертыванию
- **[CALENDAR_GUIDE.md](CALENDAR_GUIDE.md)** - интеграция с Google Calendar

### Конфигурационные файлы:
- `.env.example` - шаблон переменных окружения
- `.env.test.example` - шаблон для тестирования
- `render.yaml` - конфигурация Render
- `Procfile` - команда запуска для Render

---

## 📁 Структура проекта

```
QR platba - telegram/
├── qr.py                      # Основной production бот
├── qr_test.py                 # Тестовая версия бота
├── google_calendar.py         # Модуль Google Calendar (опционально)
├── render_keep_alive.py       # Keep-alive для Render
├── requirements.txt           # Зависимости Python
├── Procfile                   # Render deployment
├── render.yaml                # Render конфигурация
├── .env.example               # Шаблон переменных окружения
├── .gitignore                 # Игнорируемые файлы
├── README.md                  # Этот файл
├── DEPLOYMENT_GUIDE.md        # Гайд по развертыванию
├── CALENDAR_GUIDE.md          # Гайд по Calendar API
└── tests/                     # Тесты pytest
    ├── __init__.py
    ├── test_qr_generation.py  # Тесты QR генерации
    └── test_calendar.py       # Тесты Calendar модуля
```

---

## 🎯 Технические детали

### QR-код формат (SPD 1.0)

```
SPD*1.0*ACC:{IBAN}*RN:{OWNER_NAME}*AM:{amount}*CC:CZK*MSG:{service}
```

**Пример:**
```
SPD*1.0*ACC:CZ3230300000003247217010*RN:ULIANA EMELINA*AM:1500*CC:CZK*MSG:LAMINACE RAS
```

### Архитектурные особенности:
- ✅ **Асинхронность** - asyncio + python-telegram-bot 21.4
- ✅ **State management** - context.user_data для сессий
- ✅ **Manual lifecycle** - следует Context7 рекомендациям
- ✅ **Graceful shutdown** - корректное завершение и cleanup
- ✅ **Lock files** - защита от конфликтов на Render
- ✅ **Keep-alive** - предотвращение засыпания на Render Free

---

## 🔧 Требования

- **Python:** 3.11+ (рекомендуется)
- **Зависимости:**
  - python-telegram-bot 21.4
  - qrcode[pil] 7.4.2
  - python-dotenv 1.0.1
  - aiohttp 3.9.5
  - flask 2.3.3
  - pytest 7.4.3 (для тестов)

---

## 💼 Преимущества для салона

| Преимущество | Описание |
|--------------|----------|
| ⚡ **Скорость** | QR-код создается за 3 секунды |
| 🎯 **Точность** | Автоматическое заполнение реквизитов |
| 😊 **Удобство** | Клиент оплачивает одним сканированием |
| 🏦 **Совместимость** | Работает со всеми чешскими банками |
| 📊 **Аналитика** | Статистика использования |

---

## 🔒 Безопасность

**Никогда не коммитьте:**
- `.env` файлы
- Токены ботов
- API ключи
- Credentials файлы

Все критичные данные добавлены в `.gitignore`.

---

## 🆘 Поддержка и Troubleshooting

### Бот не отвечает
1. Проверьте BOT_TOKEN в `.env`
2. Убедитесь что бот запущен: `ps aux | grep qr.py`
3. Проверьте логи

### Конфликт "getUpdates"
- Остановите все другие экземпляры бота
- Дождитесь 30 секунд
- Перезапустите бота (автоматическая обработка конфликтов встроена)

### Проблемы с Render
См. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** → Troubleshooting

---

## 📈 Roadmap

- [ ] Интеграция с Fresha API
- [ ] База данных для статистики
- [ ] Мультиязычность (чешский/английский)
- [ ] Webhook режим (вместо polling)
- [ ] Docker контейнеризация

---

## 📄 Лицензия

MIT License - свободно используйте для своих проектов.

---

## � Безопасность

**⚠️ ВАЖНО:** Перед началом работы прочитайте [SECURITY.md](SECURITY.md)

### Основные правила:
- ❌ **НИКОГДА** не добавляйте `.env` или `.env.test` в git
- ✅ Используйте только `.env.example` и `.env.test.example` (с placeholder значениями)
- 🔑 Храните токены бота и API ключи только в переменных окружения
- 📝 Проверяйте `git status` перед каждым commit

### При утечке токена:
1. Немедленно отзовите токен через [@BotFather](https://t.me/botfather)
2. Создайте новый токен
3. Следуйте инструкциям в [SECURITY.md](SECURITY.md)

---

## �👨‍💻 Автор

Разработано для салона красоты **Noéme**

---

**Версия:** 2.0  
**Последнее обновление:** Октябрь 2025  
**Статус:** ✅ Production Ready
