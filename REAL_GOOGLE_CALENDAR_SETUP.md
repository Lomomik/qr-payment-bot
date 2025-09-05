# Настройка Google Calendar API для Сервера

## 🚨 ВАЖНО: Два варианта настройки

### 🖥️ Для локального тестирования (OAuth)
Используйте OAuth flow - подходит только для локального тестирования

### 🌐 Для сервера (Service Account) - РЕКОМЕНДУЕТСЯ
Service Account работает без браузера и подходит для серверного развертывания

---

## Шаг 1: Создание проекта в Google Cloud Console

1. **Перейдите в Google Cloud Console:**
   - Откройте https://console.cloud.google.com/
   - Войдите в свой Google аккаунт

2. **Создайте новый проект:**
   - Нажмите на селектор проекта в верхней части страницы
   - Нажмите "NEW PROJECT"
   - Введите название: "QR Payment Bot Calendar"
   - Нажмите "CREATE"

3. **Включите Google Calendar API:**
   - В левом меню выберите "APIs & Services" > "Library"
   - В поиске введите "Google Calendar API"
   - Нажмите на "Google Calendar API"
   - Нажмите "ENABLE"

## Шаг 2: Создание Service Account (для сервера)

1. **Создание Service Account:**
   - В левом меню выберите "APIs & Services" > "Credentials"
   - Нажмите "+ CREATE CREDENTIALS"
   - Выберите "Service account"

2. **Настройка Service Account:**
   ```
   Service account name: qr-bot-calendar
   Service account ID: qr-bot-calendar (автозаполнится)
   Description: Service account for QR Payment Bot Calendar access
   ```
   - Нажмите "CREATE AND CONTINUE"

3. **Роли (пропустить):**
   - Нажмите "CONTINUE" (роли не нужны)
   - Нажмите "DONE"

4. **Создание ключа:**
   - В списке Service Accounts найдите созданный аккаунт
   - Нажмите на email Service Account
   - Перейдите на вкладку "KEYS"
   - Нажмите "ADD KEY" > "Create new key"
   - Выберите "JSON"
   - Нажмите "CREATE"
   - Файл автоматически скачается

5. **Переименование файла:**
   - Переименуйте скачанный файл в `service-account.json`
   - Поместите в корень проекта
   - НЕ добавляйте этот файл в git!

## Шаг 3: Предоставление доступа к календарю

⚠️ **КРИТИЧЕСКИ ВАЖНО:** Service Account должен иметь доступ к вашему календарю!

1. **Найдите email Service Account:**
   - В Google Cloud Console откройте ваш Service Account
   - Скопируйте email (например: `qr-bot-calendar@your-project.iam.gserviceaccount.com`)

2. **Предоставьте доступ в Google Calendar:**
   - Откройте https://calendar.google.com/
   - В левом меню найдите ваш календарь
   - Нажмите три точки рядом с календарем > "Settings and sharing"
   - В разделе "Share with specific people" нажмите "Add people"
   - Введите email Service Account
   - Выберите права: "See all event details"
   - Нажмите "Send"

3. **Получите Calendar ID:**
   - В настройках календаря найдите раздел "Integrate calendar"
   - Скопируйте "Calendar ID" (например: `your-email@gmail.com` или специальный ID)

## Альтернативный Шаг 2-3: OAuth для локального тестирования

<details>
<summary>🖥️ Нажмите для инструкций по OAuth (только для локального тестирования)</summary>

### Шаг 2: Настройка OAuth Consent Screen

1. **Перейдите к настройке согласия:**
   - В левом меню выберите "APIs & Services" > "OAuth consent screen"

2. **Выберите тип пользователя:**
   - Выберите "External" (для тестирования)
   - Нажмите "CREATE"

3. **Заполните обязательные поля OAuth consent screen:**
   ```
   App name: QR Payment Bot
   User support email: [ваш email]
   App domain - Authorized domains: [можно оставить пустым для теста]
   Developer contact information: [ваш email]
   ```

4. **Настройка Scopes:**
   - Нажмите "ADD OR REMOVE SCOPES"
   - Найдите и добавьте: `../auth/calendar.readonly`
   - Нажмите "UPDATE"
   - Нажмите "SAVE AND CONTINUE"

5. **Test users (важно!):**
   - Добавьте ваш email в список test users
   - Нажмите "ADD USERS"
   - Введите email, который используется для Google Calendar
   - Нажмите "SAVE AND CONTINUE"

### Шаг 3: Создание OAuth 2.0 Credentials

1. **Создание учетных данных:**
   - В левом меню выберите "APIs & Services" > "Credentials"
   - Нажмите "+ CREATE CREDENTIALS"
   - Выберите "OAuth 2.0 Client IDs"

2. **Настройка OAuth client:**
   ```
   Application type: Desktop application
   Name: QR Payment Bot Calendar Access
   ```
   - Нажмите "CREATE"

3. **Скачивание credentials:**
   - В появившемся окне нажмите "DOWNLOAD JSON"
   - Сохраните файл как `credentials.json` в корне проекта
   - НЕ добавляйте этот файл в git!

</details>

## Шаг 4: Установка зависимостей

Убедитесь, что у вас установлены все необходимые пакеты:

```bash
pip install google-api-python-client==2.103.0
pip install google-auth-httplib2==0.1.1
pip install google-auth-oauthlib==1.0.0
pip install python-telegram-bot==21.4
pip install qrcode[pil]==7.4.2
pip install python-dotenv==1.0.1
```

## Шаг 5: Настройка переменных окружения

### Для Service Account (сервер):
Добавьте в `.env.test`:

```env
BOT_TOKEN=your_test_bot_token
ADMIN_TELEGRAM_ID=your_telegram_id
OWNER_NAME=ULIANA EMELINA (TEST)
ACCOUNT_NUMBER=3247217010/3030

# Google Calendar настройки
GOOGLE_CALENDAR_TYPE=service_account
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
GOOGLE_CALENDAR_ID=your-calendar-id@gmail.com
```

### Для OAuth (локальное тестирование):
Добавьте в `.env.test`:

```env
BOT_TOKEN=your_test_bot_token
ADMIN_TELEGRAM_ID=your_telegram_id
OWNER_NAME=ULIANA EMELINA (TEST)
ACCOUNT_NUMBER=3247217010/3030

# Google Calendar настройки
GOOGLE_CALENDAR_TYPE=oauth
GOOGLE_CREDENTIALS_FILE=credentials.json
```

## Шаг 6: Структура файлов

### Для Service Account (сервер):
```
QR platba - telegram/
├── service-account.json       # Service Account key (НЕ в git!)
├── google_calendar.py         # Модуль работы с календарем
├── qr_test.py                # Тестовый бот с календарем
├── .env.test                 # Переменные окружения
└── .gitignore               # Должен содержать service-account.json
```

### Для OAuth (локальное тестирование):
```
QR platba - telegram/
├── credentials.json           # OAuth credentials (НЕ в git!)
├── token.json                # Автоматически создаваемый токен (НЕ в git!)
├── google_calendar.py        # Модуль работы с календарем
├── qr_test.py               # Тестовый бот с календарем
├── .env.test                # Переменные окружения
└── .gitignore              # Должен содержать credentials.json и token.json
```

## Шаг 7: Обновление .gitignore

Добавьте в `.gitignore`:

```gitignore
# Google Calendar credentials
credentials.json
token.json
service-account.json

# Environment files
.env
.env.test
```

## Шаг 8: Первый запуск и тестирование

### Для Service Account (сервер):

1. **Убедитесь, что все файлы на месте:**
   ```bash
   ls -la service-account.json  # Должен существовать
   cat .env.test               # Проверьте переменные
   ```

2. **Тест подключения:**
   ```bash
   python test_calendar.py
   ```

3. **Запуск бота:**
   ```bash
   python qr_test.py
   ```

### Для OAuth (локальное тестирование):

1. **Запустите тестовый бот:**
   ```bash
   python qr_test.py
   ```

2. **Авторизация Google Calendar:**
   - При первом запуске откроется браузер
   - Войдите в Google аккаунт с календарем
   - Разрешите доступ к календарю
   - Вернитесь в терминал - авторизация завершена

3. **Проверка работы:**
   - Отправьте `/start` в Telegram бот
   - Нажмите "💰 Создать QR-код для оплаты"
   - Должны появиться реальные события из календаря

## Шаг 9: Тестирование

1. **Создайте тестовые события в Google Calendar:**
   ```
   Сегодня, 10:00 - Úprava obočí - Иван Петров
   Сегодня, 14:00 - Laminace řas - Мария Иванова
   Сегодня, 16:30 - Líčení - Анна Смирнова
   ```

2. **Проверьте в боте:**
   - События должны отображаться с автоматически подобранными ценами
   - QR коды должны генерироваться с правильной информацией

## Возможные проблемы и решения

### Service Account проблемы:

#### Ошибка "Calendar not found" или "Forbidden"
- ✅ Убедитесь, что предоставили доступ Service Account к календарю
- ✅ Проверьте правильность Calendar ID в `.env.test`
- ✅ Service Account email должен быть добавлен в настройки календаря

#### Ошибка "Service account key not found"
- ✅ Проверьте, что `service-account.json` существует
- ✅ Проверьте путь в переменной `GOOGLE_SERVICE_ACCOUNT_FILE`

#### Ошибка "Invalid service account key"
- ✅ Пересоздайте Service Account key в Google Cloud Console
- ✅ Убедитесь, что файл не поврежден

### OAuth проблемы:

#### Ошибка "invalid_client"
- ✅ Проверьте, что `credentials.json` загружен правильно
- ✅ Убедитесь, что OAuth consent screen настроен

#### Ошибка "access_denied"
- ✅ Добавьте ваш email в test users
- ✅ Проверьте, что scope `../auth/calendar.readonly` добавлен

### Общие проблемы:

#### "No events found"
- ✅ Убедитесь, что в календаре есть события на сегодня
- ✅ Проверьте, что используется правильный Google аккаунт
- ✅ Проверьте Calendar ID

#### Ошибка загрузки calendar_service
- ✅ Перезапустите бот после первой авторизации
- ✅ Проверьте логи на наличие ошибок аутентификации

## Дополнительные настройки

### Изменение Calendar ID
Если нужно подключить не основной календарь:

```python
# В google_calendar.py найдите и измените:
calendar_id = 'primary'  # или конкретный ID календаря
```

### Расширение прав доступа
Для создания/редактирования событий измените SCOPES:

```python
SCOPES = ['https://www.googleapis.com/auth/calendar']  # Полный доступ
```

## Безопасность

⚠️ **ВАЖНО:**
- `credentials.json` содержит секретные ключи - НЕ добавляйте в git
- `token.json` содержит токены доступа - НЕ добавляйте в git
- Для продакшена используйте Service Account вместо OAuth
- Регулярно проверяйте доступы в Google Cloud Console

## Следующие шаги

После успешной настройки вы можете:
1. Добавить больше типов процедур в `PROCEDURE_PRICES`
2. Настроить автоматическое определение клиентов
3. Интегрировать с системой бронирования
4. Добавить уведомления о записях
