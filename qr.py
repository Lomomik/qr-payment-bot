#!/usr/bin/env python3
"""
Telegram бот для генерации QR-кодов для оплаты услуг салона красоты
Работает с чешскими банками (Air Bank, Raiffeisenbank CZ)
"""

import os
import logging
import asyncio
import time
import qrcode
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Импорт модуля базы данных
try:
    from database import db
    DB_ENABLED = True
    logger.info("✅ Database module loaded successfully")
except ImportError:
    DB_ENABLED = False
    logger.warning("⚠️ Database module not found, using in-memory stats")

# Импорт keep-alive для предотвращения засыпания на Render
try:
    from render_keep_alive import setup_render_keep_alive, render_keep_alive
except ImportError:
    logger.warning("render_keep_alive module not found, keep-alive disabled")
    setup_render_keep_alive = None
    render_keep_alive = None

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID')
OWNER_NAME = os.getenv('OWNER_NAME', 'ULIANA EMELINA')
ACCOUNT_NUMBER = os.getenv('ACCOUNT_NUMBER', '3247217010/3030')
IBAN = os.getenv('IBAN', 'CZ3230300000003247217010')

# Парсим список админов (поддержка нескольких ID через запятую)
ADMIN_IDS = set()
if ADMIN_TELEGRAM_ID:
    for admin_id in ADMIN_TELEGRAM_ID.split(','):
        admin_id = admin_id.strip()
        if admin_id:
            ADMIN_IDS.add(admin_id)
    logger.info(f"✅ Loaded {len(ADMIN_IDS)} admin(s)")

def check_is_admin(user_id: int) -> bool:
    """Проверяет является ли пользователь админом"""
    return str(user_id) in ADMIN_IDS

# Статистика (fallback если БД недоступна)
user_stats = {}  # Используется только если DB_ENABLED = False

# Услуги салона - группировка по типам с понятными эмодзи
SERVICES_ALL = {
    # Услуги для бровей (🌿)
    'uprava_barveni': '🌿 ÚPRAVA A BARVENÍ',
    'uprava': '🌿 ÚPRAVA',
    'zesvetleni_uprava_tonovani': '🌿 ZESVĚTLENÍ S ÚPRAVOU A TONOVÁNÍM',
    'laminace_uprava_tonovani': '🌿 LAMINACE S ÚPRAVOU A TONOVÁNÍM',
    
    # Услуги для ресниц (👁️ и ✨)
    'laminace_ras': '👁️ LAMINACE ŘAS',
    'barveni_ras': '👁️ BARVENÍ ŘAS',
    'laminace_ras_uprava_barveni': '✨ LAMINACE ŘAS + ÚPRAVA A BARVENÍ OBOČÍ',
    'laminace_ras_zesvetleni': '✨ LAMINACE ŘAS + ZESVĚTLENÍ OBOČÍ S TÓNOVÁNÍM',
    'laminace_oboci_ras': '✨ LAMINACE OBOČÍ A ŘAS',
    'depilace_obliceje': '🌿 DEPILACE OBLIČEJE',
    # Красота и стиль (💄)
    'liceni_uces': '👄 LÍČENÍ & ÚČES',
    'liceni': '👄 LÍČENÍ',
    'uces': '👄 ÚČES',
}

# Услуги для сумм до 1000 CZK включительно
SERVICES_LOW_PRICE = {
    'uprava_barveni': '🌿 ÚPRAVA A BARVENÍ',
    'uprava': '🌿 ÚPRAVA', 
    'zesvetleni_uprava_tonovani': '🌿 ZESVĚTLENÍ S ÚPRAVOU A TONOVÁNÍM',
    'laminace_uprava_tonovani': '🌿 LAMINACE S ÚPRAVOU A TONOVÁNÍM',
    'laminace_ras': '👁️ LAMINACE ŘAS',
    'barveni_ras': '👁️ BARVENÍ ŘAS',
    'depilace_obliceje': '🌿 DEPILACE OBLIČEJE',
    'uces': '👄 ÚČES',
}

# Услуги для сумм от 1001 CZK
SERVICES_HIGH_PRICE = {
    'laminace_ras_uprava_barveni': '✨ LAMINACE ŘAS + ÚPRAVA A BARVENÍ OBOČÍ',
    'laminace_ras_zesvetleni': '✨ LAMINACE ŘAS + ZESVĚTLENÍ OBOČÍ S TÓNOVÁNÍM',
    'laminace_oboci_ras': '✨ LAMINACE OBOČÍ A ŘAS',
    'liceni_uces': '👄 LÍČENÍ & ÚČES',
    'liceni': '👄 LÍČENÍ',
}

def get_services_for_amount(amount: float) -> dict:
    """Возвращает список услуг в зависимости от суммы"""
    if amount <= 1000:
        return SERVICES_LOW_PRICE
    else:
        return SERVICES_HIGH_PRICE

def get_main_keyboard(show_admin: bool = False):
    """Создает главное меню с кнопками"""
    keyboard = [
        [KeyboardButton('💰 Создать QR-код для оплаты')],
        [KeyboardButton('ℹ️ Реквизиты счета'), KeyboardButton('❓ Помощь')]
    ]
    
    # Добавляем кнопку админ-панели для админов
    if show_admin:
        keyboard.append([KeyboardButton('🔧 Админ-панель')])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard():
    """Создает админское меню с кнопками"""
    keyboard = [
        [KeyboardButton('📊 Статистика'), KeyboardButton('🔍 Проверка БД')],
        [KeyboardButton('➕ Добавить транзакцию'), KeyboardButton('📦 Бэкап')],
        [KeyboardButton('🔙 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_services_keyboard(amount: float = None):
    """Создает клавиатуру с выбором услуг в зависимости от суммы"""
    if amount is None:
        # Используем все услуги если сумма не указана
        services = SERVICES_ALL
    else:
        # Выбираем услуги в зависимости от суммы
        services = get_services_for_amount(amount)
    
    keyboard = []
    
    # Размещаем каждую услугу в отдельной строке
    for service_key, service_name in services.items():
        keyboard.append([InlineKeyboardButton(service_name, callback_data=f"service_{service_key}")])
    
    # Добавляем кнопку "Написать услугу самому"
    keyboard.append([InlineKeyboardButton("✏️ Написать услугу самому", callback_data="service_custom")])
    
    # Добавляем кнопку "Без указания услуги"
    keyboard.append([InlineKeyboardButton("❌ Без указания услуги", callback_data="service_none")])
    
    return InlineKeyboardMarkup(keyboard)

def get_amount_keyboard():
    """Создает клавиатуру с быстрым выбором суммы"""
    keyboard = []
    amounts = range(500, 1900, 100)  # от 500 до 1800 с шагом 100
    
    # Размещаем кнопки по 3 в ряд
    row = []
    for amount in amounts:
        row.append(InlineKeyboardButton(f"{amount} CZK", callback_data=f"amount_{amount}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    # Добавляем оставшиеся кнопки если есть
    if row:
        keyboard.append(row)
    
    # Добавляем кнопку для ввода своей суммы
    keyboard.append([InlineKeyboardButton("✏️ Ввести свою сумму", callback_data="amount_custom")])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    # Определяем статус админа
    is_admin = check_is_admin(user_id)
    
    # Логируем пользователя в БД или fallback статистику
    if DB_ENABLED:
        try:
            db.add_or_update_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_admin=is_admin
            )
            db.add_event(user_id, 'start')
        except Exception as e:
            logger.error(f"Database error: {e}")
    else:
        user_stats[user_id] = user_stats.get(user_id, 0) + 1
    
    await update.message.reply_text(
        '🌿 Добро пожаловать в систему оплаты салона красоты Noéme!\n\n'
        '💰 Этот бот поможет вам быстро создать QR-код для оплаты услуг.\n\n'
        '📱 Как это работает:\n'
        '• Клиент сканирует QR-код своим банковским приложением\n'
        '• Автоматически заполняются все данные для перевода\n'
        '• Остается только подтвердить платеж\n\n'
        '👇 Выберите действие с помощью кнопок ниже:',
        reply_markup=get_main_keyboard(is_admin)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    user_id = str(update.effective_user.id)
    is_admin = check_is_admin(int(user_id))
    
    help_text = (
        '📋 <b>ИНСТРУКЦИЯ ДЛЯ СОТРУДНИКА</b>\n\n'
        '<b>Как создать QR-код:</b>\n'
        '1️⃣ Рассчитайте стоимость услуг\n'
        '2️⃣ Нажмите кнопку "💰 Создать QR-код для оплаты"\n'
        '3️⃣ Введите сумму в кронах (например: 1400)\n'
        '4️⃣ Выберите услугу из списка\n'
        '5️⃣ Покажите QR-код клиенту\n'
        '6️⃣ Клиент сканирует код в банковском приложении\n\n'
        '💡 QR-код автоматически заполнит все данные для перевода!'
    )
    
    if is_admin:
        help_text += (
            '\n\n🔧 <b>КОМАНДЫ ДЛЯ АДМИНА:</b>\n\n'
            '📊 <b>/stats</b> - Полная статистика\n'
            '   • Общая статистика за все время\n'
            '   • Статистика по месяцам (текущий и прошлый)\n'
            '   • Топ пользователей\n'
            '   • Популярные услуги\n\n'
            '➕ <b>/addtx</b> - Добавить транзакцию вручную\n'
            '   Формат: /addtx &lt;сумма&gt; &lt;username&gt; &lt;услуга&gt;\n'
            '   Пример: /addtx 1400 makkenddyy LAMINACE ŘAS\n'
            '   Пользователь должен сначала запустить бота!\n\n'
            '📦 <b>/backup</b> - Экспорт данных в JSON\n'
            '   Сохраняет все транзакции и пользователей\n'
            '   в файл для резервной копии\n\n'
            '🔍 <b>/dbcheck</b> - Диагностика базы данных\n'
            '   Проверяет подключение к PostgreSQL,\n'
            '   версию psycopg2, тип используемой БД\n\n'
            '🔧 <b>Кнопки админ-панели:</b>\n'
            '   Используйте кнопку "🔧 Админ-панель" для\n'
            '   быстрого доступа ко всем командам'
        )
    
    await update.message.reply_text(
        help_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard(is_admin)
    )

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать свой Telegram ID"""
    user = update.effective_user
    await update.message.reply_text(
        f'👤 <b>Ваша информация:</b>\n\n'
        f'🆔 Telegram ID: <code>{user.id}</code>\n'
        f'👤 Username: @{user.username or "нет"}\n'
        f'📝 Имя: {user.first_name or ""} {user.last_name or ""}\n\n'
        f'<i>Скопируйте ID для добавления в список админов</i>',
        parse_mode='HTML'
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Админ-панель (только для админа)"""
    user_id = str(update.effective_user.id)
    
    if not check_is_admin(int(user_id)):
        await update.message.reply_text('❌ У вас нет доступа к админ-панели.')
        return
    
    await update.message.reply_text(
        '🔧 <b>АДМИН-ПАНЕЛЬ</b>\n\n'
        'Выберите действие с помощью кнопок ниже:',
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /info"""
    await update.message.reply_text(
        f'📋 **РЕКВИЗИТЫ СЧЕТА САЛОНА**\n\n'
        f'👤 **Получатель:** {OWNER_NAME}\n'
        f'🏦 **Номер счета:** {ACCOUNT_NUMBER}\n'
        f'🌍 **IBAN:** {IBAN}\n'
        f'💱 **Валюта:** CZK (чешские кроны)\n\n'
        f'💰 Для создания QR-кода нажмите соответствующую кнопку ниже',
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для создания QR-кода для оплаты"""
    user = update.effective_user
    user_id = user.id
    
    # Логируем в БД
    if DB_ENABLED:
        try:
            db.add_or_update_user(user_id, user.username, user.first_name, user.last_name)
            db.add_event(user_id, 'payment_start')
        except Exception as e:
            logger.error(f"Database error: {e}")
    else:
        user_stats[user_id] = user_stats.get(user_id, 0) + 1
    
    await update.message.reply_text(
        '🌿 <b>Создание QR-кода для оплаты</b>\n\n'
        '<b>Шаги:</b>\n'
        '1️⃣ Посмотрите сумму за услугу в <b>Fresha Partner</b>\n'
        '2️⃣ Выберите сумму из списка или введите свою\n'
        '3️⃣ Выберите услугу\n'
        '4️⃣ Покажите QR-код клиенту\n\n'
        '👇 <b>Выберите сумму или введите свою:</b>',
        reply_markup=get_amount_keyboard(),
        parse_mode='HTML'
    )
    
    # Устанавливаем состояние ожидания суммы
    context.user_data['waiting_for_amount'] = True

def generate_qr_code(amount: float, service_msg: str = None) -> BytesIO:
    """Генерирует QR-код с данными для оплаты"""
    # Точный формат Air Bank с услугой
    # Формат: SPD*1.0*ACC:CZ3230300000003247217010*RN:ULIANA EMELINA*AM:500*CC:CZK*MSG:ZESVETLENI OBOCI
    
    # Форматируем сумму как целое число если это возможно, иначе с запятой
    if amount == int(amount):
        formatted_amount = str(int(amount))
    else:
        formatted_amount = f"{amount:.2f}".replace('.', ',')
    
    # Создаем базовый QR текст
    qr_text = f"SPD*1.0*ACC:{IBAN}*RN:{OWNER_NAME.upper()}*AM:{formatted_amount}*CC:CZK"
    
    # Добавляем услугу если указана
    if service_msg:
        qr_text += f"*MSG:{service_msg}"
    
    # Создаем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    
    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохраняем в BytesIO
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    return bio

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений (кнопки и суммы)"""
    text = update.message.text
    user_id = str(update.effective_user.id)
    is_admin = check_is_admin(int(user_id))
    
    # Обработка основных кнопок
    if text == '💰 Создать QR-код для оплаты':
        await payment_command(update, context)
        return
    elif text == 'ℹ️ Реквизиты счета':
        await info_command(update, context)
        return
    elif text == '❓ Помощь':
        await help_command(update, context)
        return
    
    # Обработка кнопок админ-панели
    elif text == '🔧 Админ-панель' and check_is_admin(int(user_id)):
        await admin_command(update, context)
        return
    elif text == '📊 Статистика' and check_is_admin(int(user_id)):
        await stats_command(update, context)
        return
    elif text == '🔍 Проверка БД' and check_is_admin(int(user_id)):
        await dbcheck_command(update, context)
        return
    elif text == '➕ Добавить транзакцию' and check_is_admin(int(user_id)):
        await update.message.reply_text(
            '➕ <b>Добавление транзакции</b>\n\n'
            'Формат: /addtx &lt;сумма&gt; &lt;username&gt; &lt;услуга&gt;\n\n'
            '<b>Пример:</b>\n'
            '/addtx 1400 makkenddyy LAMINACE ŘAS\n\n'
            '<i>Пользователь должен сначала запустить бота!</i>',
            parse_mode='HTML',
            reply_markup=get_admin_keyboard()
        )
        return
    elif text == '📦 Бэкап' and check_is_admin(int(user_id)):
        await backup_command(update, context)
        return
    elif text == '🔙 Главное меню':
        await update.message.reply_text(
            '🔙 Возвращаемся в главное меню',
            reply_markup=get_main_keyboard(is_admin)
        )
        return
    
    # Обработка ввода суммы
    if context.user_data.get('waiting_for_amount'):
        await handle_amount(update, context)
    # Обработка ввода пользовательской услуги
    elif context.user_data.get('waiting_for_custom_service'):
        await handle_custom_service(update, context)
    else:
        await update.message.reply_text(
            '❓ Используйте кнопки для навигации или команды:\n\n'
            '💰 Создать QR-код - для создания QR-кода\n'
            'ℹ️ Реквизиты счета - для просмотра реквизитов\n'
            '❓ Помощь - для получения инструкций',
            reply_markup=get_main_keyboard(is_admin)
        )

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода суммы"""
    try:
        # Парсим сумму
        amount_text = update.message.text.strip().replace(',', '.')
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text(
                '❌ Сумма должна быть больше нуля!\n'
                'Попробуйте еще раз:'
            )
            return
        
        if amount > 1000000:
            await update.message.reply_text(
                '❌ Сумма слишком большая!\n'
                'Максимум: 1,000,000 CZK'
            )
            return
        
        # Сохраняем сумму в контексте пользователя
        context.user_data['amount'] = amount
        context.user_data['waiting_for_amount'] = False
        context.user_data['waiting_for_service'] = True
        
        # Форматируем сумму для отображения
        formatted_amount = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        
        # Показываем выбор услуг с учетом суммы
        await update.message.reply_text(
            f'💰 Сумма: {formatted_amount} CZK\n\n'
            '🌿 Выберите услугу для указания в платеже:\n'
            '👇 Нажмите на нужную услугу',
            reply_markup=get_services_keyboard(amount)
        )
        
        logger.info(f"Amount {amount} CZK saved, waiting for service selection, user: {update.effective_user.id}")
        
    except ValueError:
        await update.message.reply_text(
            '❌ Неверный формат суммы!\n\n'
            '📝 Используйте:\n'
            '• Целые числа: 500, 1000\n'
            '• Десятичные: 500.50, 1000.25\n\n'
            'Попробуйте еще раз:'
        )

async def handle_custom_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода пользовательской услуги"""
    service_text = update.message.text.strip()
    
    if len(service_text) < 2:
        await update.message.reply_text(
            '❌ Название услуги слишком короткое!\n'
            'Попробуйте еще раз:'
        )
        return
    
    if len(service_text) > 50:
        await update.message.reply_text(
            '❌ Название услуги слишком длинное!\n'
            'Максимум: 50 символов\n'
            'Попробуйте еще раз:'
        )
        return
    
    # Получаем сумму из контекста
    amount = context.user_data.get('amount')
    if not amount:
        await update.message.reply_text('❌ Ошибка: сумма не найдена.')
        return
    
    # Очищаем название услуги (убираем лишние пробелы, приводим к верхнему регистру)
    service_msg = service_text.upper().strip()
    
    # Генерируем QR-код с пользовательской услугой
    qr_image = generate_qr_code(amount, service_msg)
    
    # Форматируем сумму для отображения
    formatted_amount = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    
    # Отправляем QR-код
    await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=qr_image,
        caption=f'🌿 QR-код для оплаты услуг салона\n\n'
               f'💰 Сумма: {formatted_amount} CZK\n'
               f'🛍️ Услуга: {service_msg}\n'
               f'👤 Получатель: {OWNER_NAME}\n'
               f'🏦 Счет: {ACCOUNT_NUMBER}\n\n'
               f'📱 Покажите этот QR-код клиенту\n'
               f'✅ Клиент сканирует код в своем банковским приложением',
        reply_markup=get_main_keyboard()
    )
    
    # Записываем транзакцию в БД
    if DB_ENABLED:
        try:
            db.add_transaction(
                user_id=update.effective_user.id,
                amount=amount,
                service=service_msg
            )
            db.add_event(update.effective_user.id, 'qr_generated', f'amount:{amount},service:{service_msg}')
        except Exception as e:
            logger.error(f"Database error when saving transaction: {e}")
    
    # Сбрасываем состояние
    context.user_data['waiting_for_service'] = False
    context.user_data['waiting_for_custom_service'] = False
    context.user_data['amount'] = None
    
    logger.info(f"QR code generated for amount: {amount} CZK, custom service: {service_msg}, user: {update.effective_user.id}")

async def handle_amount_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора суммы через кнопки"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get('waiting_for_amount'):
        await query.edit_message_text('❌ Ошибка: неожиданный выбор суммы.')
        return
    
    if query.data == 'amount_custom':
        # Пользователь хочет ввести свою сумму
        await query.edit_message_text(
            '✏️ <b>Введите свою сумму</b>\n\n'
            '📝 Используйте:\n'
            '• Целые числа: 500, 1000\n'
            '• Десятичные: 500.50, 1000.25\n\n'
            '👇 Напишите сумму для оплаты:',
            parse_mode='HTML'
        )
        # Состояние остается waiting_for_amount=True для ввода текста
        return
    
    # Извлекаем сумму из callback_data
    amount_str = query.data.replace('amount_', '')
    try:
        amount = float(amount_str)
        
        # Сохраняем сумму в контексте пользователя
        context.user_data['amount'] = amount
        context.user_data['waiting_for_amount'] = False
        context.user_data['waiting_for_service'] = True
        
        # Форматируем сумму для отображения
        formatted_amount = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        
        # Показываем выбор услуг с учетом суммы
        await query.edit_message_text(
            f'💰 Сумма: {formatted_amount} CZK\n\n'
            '🌿 Выберите услугу для указания в платеже:\n'
            '👇 Нажмите на нужную услугу',
            reply_markup=get_services_keyboard(amount)
        )
        
        logger.info(f"Amount {amount} CZK selected via button, waiting for service selection, user: {update.effective_user.id}")
        
    except ValueError:
        await query.edit_message_text('❌ Ошибка: неверная сумма.')

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора услуги"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get('waiting_for_service'):
        await query.edit_message_text('❌ Ошибка: сначала введите сумму.')
        return
    
    amount = context.user_data.get('amount')
    if not amount:
        await query.edit_message_text('❌ Ошибка: сумма не найдена.')
        return
    
    # Получаем выбранную услугу
    service_key = query.data.replace('service_', '')
    
    if service_key == 'none':
        service_name = None
        service_msg = None
        caption_service = ''
    elif service_key == 'custom':
        # Пользователь хочет ввести свою услугу
        await query.edit_message_text(
            '✏️ <b>Введите название услуги</b>\n\n'
            '📝 Например:\n'
            '• ÚPRAVA OBOČÍ\n'
            '• BARVENÍ ŘAS\n'
            '• KOMBINACE SLUŽEB\n\n'
            '👇 Напишите название услуги:',
            parse_mode='HTML'
        )
        # Устанавливаем состояние ожидания услуги
        context.user_data['waiting_for_custom_service'] = True
        return
    else:
        # Ищем услугу во всех доступных услугах
        service_name = SERVICES_ALL.get(service_key)
        if service_name:
            # Убираем эмодзи из названия для QR-кода
            service_msg = service_name.split(' ', 1)[1] if ' ' in service_name else service_name
            caption_service = f'🛍️ Услуга: {service_msg}\n'
        else:
            service_name = None
            service_msg = None
            caption_service = ''
    
    # Генерируем QR-код с услугой
    qr_image = generate_qr_code(amount, service_msg)
    
    # Форматируем сумму для отображения
    formatted_amount = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    
    # Удаляем предыдущее сообщение и отправляем QR-код
    await query.delete_message()
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=qr_image,
        caption=f'🌿 QR-код для оплаты услуг салона\n\n'
               f'💰 Сумма: {formatted_amount} CZK\n'
               f'{caption_service}'
               f'👤 Получатель: {OWNER_NAME}\n'
               f'🏦 Счет: {ACCOUNT_NUMBER}\n\n'
               f'📱 Покажите этот QR-код клиенту\n'
               f'✅ Клиент сканирует код в своем банковском приложении',
        reply_markup=get_main_keyboard()
    )
    
    # Записываем транзакцию в БД
    if DB_ENABLED:
        try:
            db.add_transaction(
                user_id=update.effective_user.id,
                amount=amount,
                service=service_msg if service_msg else None
            )
            db.add_event(update.effective_user.id, 'qr_generated', f'amount:{amount},service:{service_msg}')
        except Exception as e:
            logger.error(f"Database error when saving transaction: {e}")
    
    # Сбрасываем состояние
    context.user_data['waiting_for_service'] = False
    context.user_data['amount'] = None
    
    service_log = service_name if service_name else "without service"
    logger.info(f"QR code generated for amount: {amount} CZK, service: {service_log}, user: {update.effective_user.id}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика использования (только для админа)"""
    user_id = str(update.effective_user.id)
    
    if not check_is_admin(int(user_id)):
        await update.message.reply_text('❌ У вас нет доступа к этой команде.')
        return
    
    if DB_ENABLED:
        try:
            # Получаем данные из БД
            total_stats = db.get_total_stats()
            all_users = db.get_all_users_stats()
            popular_services = db.get_popular_services(5)
            
            # Получаем месячную статистику
            current_month = db.get_monthly_stats(0)  # Текущий месяц
            prev_month = db.get_monthly_stats(1)     # Прошлый месяц
            
            # Показываем тип базы данных
            db_icon = "🐘" if db.db_type == 'postgresql' else "📝"
            db_name = "PostgreSQL" if db.db_type == 'postgresql' else "SQLite"
            
            # Названия месяцев
            month_names = ['', 'январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 
                          'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
            
            stats_text = f'📊 **СТАТИСТИКА БОТА**\n'
            stats_text += f'{db_icon} База данных: **{db_name}**\n\n'
            
            stats_text += f'**📅 За все время:**\n'
            stats_text += f'👥 Всего пользователей: {total_stats["total_users"]}\n'
            stats_text += f'💰 Всего транзакций: {total_stats["total_transactions"]}\n'
            stats_text += f'💵 Общая сумма: {total_stats["total_amount"]:,.0f} CZK\n'
            stats_text += f'📊 Средняя сумма: {total_stats["avg_amount"]:.0f} CZK\n'
            stats_text += f'🟢 Активных за 24ч: {total_stats["active_24h"]}\n\n'
            
            # Текущий месяц
            if current_month['transactions'] > 0:
                curr_month_name = month_names[current_month['month']]
                stats_text += f'**📅 {curr_month_name.capitalize()} {current_month["year"]}:**\n'
                stats_text += f'💰 Транзакций: {current_month["transactions"]}\n'
                stats_text += f'💵 Сумма: {current_month["total_amount"]:,.0f} CZK\n'
                stats_text += f'📊 Средняя: {current_month["avg_amount"]:.0f} CZK\n'
                stats_text += f'👥 Клиентов: {current_month["unique_users"]}\n\n'
            
            # Прошлый месяц
            if prev_month['transactions'] > 0:
                prev_month_name = month_names[prev_month['month']]
                stats_text += f'**📅 {prev_month_name.capitalize()} {prev_month["year"]}:**\n'
                stats_text += f'💰 Транзакций: {prev_month["transactions"]}\n'
                stats_text += f'💵 Сумма: {prev_month["total_amount"]:,.0f} CZK\n'
                stats_text += f'📊 Средняя: {prev_month["avg_amount"]:.0f} CZK\n'
                stats_text += f'👥 Клиентов: {prev_month["unique_users"]}\n\n'
            
            if all_users:
                stats_text += '**Топ пользователей:**\n'
                for i, user in enumerate(all_users[:5], 1):
                    username = user['username'] or f"ID{user['user_id']}"
                    stats_text += f'{i}. @{username}: {user["transactions_count"]} QR, {user["total_amount"]:.0f} CZK\n'
            
            if popular_services:
                stats_text += '\n**Популярные услуги:**\n'
                for i, (service, count) in enumerate(popular_services, 1):
                    stats_text += f'{i}. {service}: {count}x\n'
            
            # Создаем кнопки для выбора других месяцев
            keyboard = []
            keyboard.append([
                InlineKeyboardButton("📅 Другой месяц", callback_data="stats_select_month")
            ])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Database error in stats: {e}")
            await update.message.reply_text(f'❌ Ошибка получения статистики из БД: {e}')
    else:
        # Fallback на старую статистику в памяти
        total_users = len(user_stats)
        total_requests = sum(user_stats.values())
        
        stats_text = f'📊 **СТАТИСТИКА БОТА (память)**\n\n'
        stats_text += f'👥 Всего пользователей: {total_users}\n'
        stats_text += f'📱 Всего запросов: {total_requests}\n\n'
        
        if user_stats:
            stats_text += '**Топ пользователей:**\n'
            sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)
            for i, (uid, count) in enumerate(sorted_users[:5], 1):
                stats_text += f'{i}. User {uid}: {count} запросов\n'
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

async def handle_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для выбора месяца статистики"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if not check_is_admin(int(user_id)):
        await query.edit_message_text('❌ У вас нет доступа к этой команде.')
        return
    
    if query.data == "stats_select_month":
        # Показываем список последних 12 месяцев
        from datetime import datetime, timedelta
        
        keyboard = []
        month_names = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        
        # Генерируем кнопки для последних 12 месяцев
        row = []
        for offset in range(12):
            target_date = datetime.now() - timedelta(days=30 * offset)
            month_name = month_names[target_date.month]
            year = target_date.year
            
            button_text = f"{month_name} {year}"
            row.append(InlineKeyboardButton(button_text, callback_data=f"stats_month_{offset}"))
            
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="stats_back")])
        
        await query.edit_message_text(
            '📅 <b>Выберите месяц:</b>',
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith("stats_month_"):
        # Показываем статистику за выбранный месяц
        offset = int(query.data.split('_')[2])
        
        if DB_ENABLED:
            try:
                from datetime import datetime, timedelta
                month_stats = db.get_monthly_stats(offset)
                
                month_names = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                              'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
                
                month_name = month_names[month_stats['month']]
                
                stats_text = f'📊 <b>Статистика за {month_name} {month_stats["year"]}</b>\n\n'
                
                if month_stats['transactions'] > 0:
                    stats_text += f'💰 Транзакций: {month_stats["transactions"]}\n'
                    stats_text += f'💵 Общая сумма: {month_stats["total_amount"]:,.0f} CZK\n'
                    stats_text += f'📊 Средний чек: {month_stats["avg_amount"]:.0f} CZK\n'
                    stats_text += f'👥 Клиентов: {month_stats["unique_users"]}\n'
                else:
                    stats_text += '📭 Нет данных за этот период'
                
                keyboard = [[InlineKeyboardButton("📅 Другой месяц", callback_data="stats_select_month")]]
                
                await query.edit_message_text(
                    stats_text,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error getting month stats: {e}")
                await query.edit_message_text(f'❌ Ошибка: {e}')
    
    elif query.data == "stats_back":
        # Возвращаемся к общей статистике
        await query.delete_message()

async def addtx_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавить транзакцию вручную (только для админа)
    Формат: /addtx <сумма> <username> <услуга>
    Пример: /addtx 1400 @makkenddyy ÚPRAVA A BARVENÍ
    """
    user_id = str(update.effective_user.id)
    
    if not check_is_admin(int(user_id)):
        await update.message.reply_text('❌ У вас нет доступа к этой команде.')
        return
    
    if not DB_ENABLED:
        await update.message.reply_text('❌ База данных не подключена.')
        return
    
    # Парсим аргументы
    try:
        args = update.message.text.split(maxsplit=3)
        if len(args) < 3:
            await update.message.reply_text(
                '❌ Неверный формат!\n\n'
                'Использование:\n'
                '/addtx <сумма> <username> [услуга]\n\n'
                'Примеры:\n'
                '/addtx 1400 @makkenddyy LAMINACE ŘAS\n'
                '/addtx 500 @user123\n'
            )
            return
        
        amount = float(args[1])
        username_arg = args[2].lstrip('@')
        service = args[3] if len(args) > 3 else None
        
        # Ищем пользователя по username
        all_users = db.get_all_users_stats()
        target_user = None
        for user in all_users:
            if user['username'] == username_arg:
                target_user = user
                break
        
        if not target_user:
            await update.message.reply_text(
                f'❌ Пользователь @{username_arg} не найден в базе.\n\n'
                'Пользователь должен сначала запустить бота (/start).'
            )
            return
        
        # Добавляем транзакцию
        db.add_transaction(target_user['user_id'], amount, service)
        
        await update.message.reply_text(
            f'✅ Транзакция добавлена!\n\n'
            f'💰 Сумма: {amount:,.0f} CZK\n'
            f'👤 Пользователь: @{username_arg}\n'
            f'🛍️ Услуга: {service or "не указана"}'
        )
        
    except ValueError:
        await update.message.reply_text('❌ Неверная сумма! Используйте число.')
    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        await update.message.reply_text(f'❌ Ошибка: {e}')

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Экспорт данных из БД в JSON (только для админа)"""
    user_id = str(update.effective_user.id)
    
    if not check_is_admin(int(user_id)):
        await update.message.reply_text('❌ У вас нет доступа к этой команде.')
        return
    
    if not DB_ENABLED:
        await update.message.reply_text('❌ База данных не подключена.')
        return
    
    try:
        import json
        from datetime import datetime
        
        # Собираем все данные
        all_users = db.get_all_users_stats()
        recent_transactions = db.get_recent_transactions(100)  # Все транзакции
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'db_type': db.db_type,
            'users': all_users,
            'transactions': recent_transactions
        }
        
        # Конвертируем в JSON
        json_data = json.dumps(backup_data, indent=2, ensure_ascii=False, default=str)
        
        # Отправляем как файл
        from io import BytesIO
        backup_file = BytesIO(json_data.encode('utf-8'))
        backup_file.name = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        await update.message.reply_document(
            document=backup_file,
            caption=f'📦 Бэкап базы данных\n\n'
                   f'Пользователей: {len(all_users)}\n'
                   f'Транзакций: {len(recent_transactions)}\n'
                   f'Дата: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await update.message.reply_text(f'❌ Ошибка создания бэкапа: {e}')

async def dbcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка подключения к базе данных (только для админа)"""
    user_id = str(update.effective_user.id)
    
    if not check_is_admin(int(user_id)):
        await update.message.reply_text('❌ У вас нет доступа к этой команде.')
        return
    
    check_text = '🔍 <b>ДИАГНОСТИКА БАЗЫ ДАННЫХ</b>\n\n'
    
    # Проверка DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Скрываем пароль
        if '@' in database_url:
            parts = database_url.split('@')
            user_part = parts[0].split('://')[0] + '://' + parts[0].split('://')[1].split(':')[0] + ':***'
            masked_url = user_part + '@' + parts[1]
        else:
            masked_url = database_url
        check_text += f'📋 DATABASE_URL: <code>{masked_url}</code>\n\n'
    else:
        check_text += '❌ DATABASE_URL: не установлен\n\n'
    
    # Проверка psycopg2
    try:
        import psycopg2
        check_text += '✅ psycopg2: установлен\n'
        check_text += f'   Версия: {psycopg2.__version__}\n\n'
    except ImportError:
        check_text += '❌ psycopg2: НЕ установлен\n\n'
    
    # Проверка типа БД
    if DB_ENABLED:
        from database import db
        check_text += f'📊 Тип БД: <b>{db.db_type.upper()}</b>\n'
        
        if db.db_type == 'postgresql':
            check_text += '🐘 PostgreSQL активен\n'
            try:
                # Пробуем подключиться
                with db.get_connection() as conn:
                    check_text += '✅ Подключение: успешно\n'
            except Exception as e:
                check_text += f'❌ Подключение: ошибка\n'
                check_text += f'   {str(e)[:100]}\n'
        else:
            check_text += '📝 SQLite активен (fallback)\n'
            if database_url and database_url.startswith('postgres'):
                check_text += '\n⚠️ <b>ПРОБЛЕМА:</b>\n'
                check_text += 'DATABASE_URL настроен, но используется SQLite!\n'
                check_text += 'Возможно psycopg2 не установлен.\n'
    else:
        check_text += '❌ База данных: не инициализирована\n'
    
    await update.message.reply_text(check_text, parse_mode='HTML')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок согласно рекомендациям Context7"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Сбрасываем состояние пользователя при ошибке
    if update and update.effective_user:
        context.user_data.clear()
    
    # Отправляем сообщение пользователю только если update доступен
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                '❌ Произошла ошибка. Попробуйте начать заново.',
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        '❓ Неизвестная команда!\n\n'
        '👇 Используйте кнопки ниже для навигации:',
        reply_markup=get_main_keyboard()
    )

def main():
    """Главная функция"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    # Проверяем единственность экземпляра на Render с улучшенным контролем
    lock_file = '/tmp/qr_bot.lock' if os.getenv('RENDER') else None
    
    if lock_file:
        try:
            if os.path.exists(lock_file):
                # Читаем PID старого процесса
                with open(lock_file, 'r') as f:
                    old_pid = f.read().strip()
                
                # Проверяем возраст lock файла
                import time
                lock_age = time.time() - os.path.getmtime(lock_file)
                
                if lock_age > 180:  # 3 минуты (более агрессивно)
                    logger.warning(f"⚠️ Removing stale lock file (>3 minutes old, PID: {old_pid})")
                    os.remove(lock_file)
                else:
                    logger.error(f"❌ Another bot instance is running (PID: {old_pid}, age: {lock_age:.0f}s)")
                    logger.info("🔄 Waiting for old instance to shutdown gracefully...")
                    
                    # Даем старому процессу 30 секунд на graceful shutdown
                    import time
                    for i in range(30):
                        time.sleep(1)
                        if not os.path.exists(lock_file):
                            logger.info("✅ Old instance shutdown detected")
                            break
                        if i == 29:
                            logger.warning("⚠️ Force removing lock file after 30s wait")
                            os.remove(lock_file)
            
            # Создаем lock файл с текущим PID
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"🔒 Lock file created with PID: {os.getpid()}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not manage lock file: {e}")
    
    logger.info("Starting QR Payment Bot...")
    
    # Инициализируем переменную для keep-alive задачи
    keep_alive_task = None
    
    # Создаем приложение БЕЗ post_init callback
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("payment", payment_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("addtx", addtx_command))
    application.add_handler(CommandHandler("dbcheck", dbcheck_command))
    
    # Обработчик для выбора сумм (inline кнопки)
    application.add_handler(CallbackQueryHandler(handle_amount_selection, pattern=r'^amount_'))
    
    # Обработчик для выбора услуг (inline кнопки)
    application.add_handler(CallbackQueryHandler(handle_service_selection, pattern=r'^service_'))
    
    # Обработчик для статистики по месяцам (inline кнопки)
    application.add_handler(CallbackQueryHandler(handle_stats_callback, pattern=r'^stats_'))
    
    # Обработчик для текстовых сообщений (кнопки и суммы)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Обработчик для неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Добавляем обработчик ошибок (Context7 рекомендация)
    application.add_error_handler(error_handler)
    
    # Запускаем бота с manual lifecycle management согласно Context7
    logger.info("Starting bot...")
    
    async def run_bot():
        """Manual lifecycle management согласно Context7 рекомендациям"""
        nonlocal keep_alive_task
        
        try:
            # Manual initialization
            await application.initialize()
            await application.start()
            
            # Проверяем на конфликты при запуске polling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await application.updater.start_polling()
                    break  # Успешно запущен
                except Exception as e:
                    if "Conflict" in str(e) and "getUpdates" in str(e):
                        logger.warning(f"🔄 Telegram API conflict detected (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            logger.info("⏳ Waiting 10 seconds for old instance to shutdown...")
                            await asyncio.sleep(10)
                            continue
                        else:
                            logger.error("❌ Failed to resolve Telegram API conflict after all retries")
                            raise
                    else:
                        raise  # Другая ошибка, не связанная с конфликтом
            
            # Настройка keep-alive ПОСЛЕ запуска event loop
            if os.getenv('RENDER') and setup_render_keep_alive:
                try:
                    keep_alive_coro = setup_render_keep_alive()
                    keep_alive_task = asyncio.create_task(keep_alive_coro)
                    logger.info("✅ Render keep-alive activated after event loop start")
                except Exception as e:
                    logger.warning(f"⚠️ Keep-alive setup failed: {e}")
            elif os.getenv('RENDER'):
                logger.warning("⚠️ Running on Render but keep-alive module not available")
            
            # Держим бота активным
            logger.info("🤖 Bot is running... Press Ctrl+C to stop")
            try:
                # Бесконечный цикл для поддержания работы
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down gracefully...")
                
        finally:
            # Manual shutdown
            logger.info("🔄 Starting graceful shutdown...")
            
            # Останавливаем keep-alive задачу
            if keep_alive_task and not keep_alive_task.done():
                keep_alive_task.cancel()
                try:
                    await keep_alive_task
                except asyncio.CancelledError:
                    logger.info("Keep-alive task cancelled")
            
            # Останавливаем render keep-alive instance
            if os.getenv('RENDER') and render_keep_alive:
                render_keep_alive.stop()
            
            # Manual shutdown sequence
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            
            logger.info("✅ Graceful shutdown completed")
    
    # Запускаем асинхронную функцию
    try:
        asyncio.run(run_bot())
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        # Удаляем lock файл
        lock_file = '/tmp/qr_bot.lock' if os.getenv('RENDER') else None
        if lock_file and os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                logger.info("🗑️ Lock file removed")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove lock file: {e}")
        
        logger.info("Bot stopped.")

if __name__ == '__main__':
    main()
