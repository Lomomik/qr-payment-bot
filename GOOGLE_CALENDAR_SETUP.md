# Google Calendar API Setup Instructions

## 1. Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Calendar API:
   - Перейдите в "APIs & Services" > "Library"
   - Найдите "Google Calendar API"
   - Нажмите "Enable"

## 2. Создание учетных данных

1. Перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" > "OAuth 2.0 Client IDs"
3. Выберите "Desktop application"
4. Дайте имя (например, "QR Payment Bot")
5. Скачайте JSON файл с учетными данными
6. Переименуйте его в `credentials.json` и поместите в корень проекта

## 3. Настройка OAuth Consent Screen

1. Перейдите в "APIs & Services" > "OAuth consent screen"
2. Выберите "External" (если нет G Suite)
3. Заполните обязательные поля:
   - App name: "QR Payment Bot"
   - User support email: ваш email
   - Developer contact email: ваш email
4. Добавьте scope: `../auth/calendar.readonly`
5. Добавьте test users (ваш email для доступа к календарю)

## 4. Структура файлов

```
QR platba - telegram/
├── credentials.json        # OAuth credentials (не добавлять в git!)
├── token.pickle           # Сохраненный токен авторизации (создается автоматически)
├── google_calendar.py     # Модуль работы с календарем
├── qr_test.py            # Тестовый бот с интеграцией
└── .env.test             # Переменные окружения
```

## 5. Переменные окружения (.env.test)

Добавьте в `.env.test`:

```env
BOT_TOKEN=your_test_bot_token
ADMIN_TELEGRAM_ID=your_telegram_id
OWNER_NAME=ULIANA EMELINA (TEST)
ACCOUNT_NUMBER=3247217010/3030
GOOGLE_CALENDAR_ID=primary
```

## 6. Первый запуск

1. Установите зависимости: `pip install -r requirements.txt`
2. Запустите тестовый бот: `python qr_test.py`
3. При первом запуске откроется браузер для авторизации Google
4. Разрешите доступ к календарю
5. Токен сохранится в `token.pickle` для последующих запусков

## 7. Тестирование без Google Calendar

Если Google Calendar недоступен, бот автоматически использует тестовые данные из функции `get_mock_today_events()`.

## 8. Безопасность

- Добавьте в `.gitignore`:
  ```
  credentials.json
  token.pickle
  ```
- Никогда не коммитьте эти файлы в репозиторий
- Для продакшена используйте Service Account или другие безопасные методы авторизации
