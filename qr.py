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

def get_main_keyboard():
    """Создает главное меню с кнопками"""
    keyboard = [
        [KeyboardButton('💰 Создать QR-код для оплаты')],
        [KeyboardButton('ℹ️ Реквизиты счета'), KeyboardButton('❓ Помощь')]
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
    
    # Логируем пользователя в БД или fallback статистику
    if DB_ENABLED:
        try:
            db.add_or_update_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_admin=(str(user_id) == ADMIN_TELEGRAM_ID)
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
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        '📋 **ИНСТРУКЦИЯ ДЛЯ СОТРУДНИКА**\n\n'
        '**Как создать QR-код:**\n'
        '1️⃣ Рассчитайте стоимость услуг\n'
        '2️⃣ Нажмите кнопку "💰 Создать QR-код для оплаты"\n'
        '3️⃣ Введите сумму в кронах (например: 1400)\n'
        '4️⃣ Выберите услугу из списка или "Без указания услуги"\n'
        '5️⃣ Покажите QR-код клиенту\n'
        '6️⃣ Клиент сканирует код в своем банковском приложении\n\n'
        '💡 QR-код автоматически заполнит все данные для перевода!',
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
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
    
    # Обработка кнопок
    if text == '💰 Создать QR-код для оплаты':
        await payment_command(update, context)
        return
    elif text == 'ℹ️ Реквизиты счета':
        await info_command(update, context)
        return
    elif text == '❓ Помощь':
        await help_command(update, context)
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
            reply_markup=get_main_keyboard()
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
    
    if user_id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text('❌ У вас нет доступа к этой команде.')
        return
    
    if DB_ENABLED:
        try:
            # Получаем данные из БД
            total_stats = db.get_total_stats()
            all_users = db.get_all_users_stats()
            popular_services = db.get_popular_services(5)
            
            stats_text = f'📊 **СТАТИСТИКА БОТА (БД)**\n\n'
            stats_text += f'👥 Всего пользователей: {total_stats["total_users"]}\n'
            stats_text += f'💰 Всего транзакций: {total_stats["total_transactions"]}\n'
            stats_text += f'💵 Общая сумма: {total_stats["total_amount"]:,.0f} CZK\n'
            stats_text += f'📊 Средняя сумма: {total_stats["avg_amount"]:.0f} CZK\n'
            stats_text += f'🟢 Активных за 24ч: {total_stats["active_24h"]}\n\n'
            
            if all_users:
                stats_text += '**Топ пользователей:**\n'
                for i, user in enumerate(all_users[:5], 1):
                    username = user['username'] or f"ID{user['user_id']}"
                    stats_text += f'{i}. @{username}: {user["transactions_count"]} QR, {user["total_amount"]:.0f} CZK\n'
            
            if popular_services:
                stats_text += '\n**Популярные услуги:**\n'
                for i, (service, count) in enumerate(popular_services, 1):
                    stats_text += f'{i}. {service}: {count}x\n'
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
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
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("payment", payment_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Обработчик для выбора сумм (inline кнопки)
    application.add_handler(CallbackQueryHandler(handle_amount_selection, pattern=r'^amount_'))
    
    # Обработчик для выбора услуг (inline кнопки)
    application.add_handler(CallbackQueryHandler(handle_service_selection, pattern=r'^service_'))
    
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
