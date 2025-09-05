#!/usr/bin/env python3
"""
Telegram бот для генерации QR-кодов для оплаты услуг салона красоты
Работает с чешскими банками (Air Bank, Raiffeisenbank CZ)
"""

import os
import logging
import asyncio
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

# Импорт keep-alive для предотвращения засыпания на Render
try:
    from render_keep_alive import setup_render_keep_alive
except ImportError:
    logger.warning("render_keep_alive module not found, keep-alive disabled")
    setup_render_keep_alive = None

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID')
OWNER_NAME = os.getenv('OWNER_NAME', 'ULIANA EMELINA')
ACCOUNT_NUMBER = os.getenv('ACCOUNT_NUMBER', '3247217010/3030')
IBAN = 'CZ3230300000003247217010'

# Статистика
user_stats = {}

# Услуги салона - группировка по типам с понятными эмодзи
SERVICES = {
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

def get_main_keyboard():
    """Создает главное меню с кнопками"""
    keyboard = [
        [KeyboardButton('💰 Создать QR-код для оплаты')],
        [KeyboardButton('ℹ️ Реквизиты счета'), KeyboardButton('❓ Помощь')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_services_keyboard():
    """Создает клавиатуру с выбором услуг"""
    keyboard = []
    services_list = list(SERVICES.items())
    
    # Первые услуги по одной в ряд
    for i in range(len(services_list) - 4):
        service_key, service_name = services_list[i]
        keyboard.append([InlineKeyboardButton(service_name, callback_data=f"service_{service_key}")])
    
    # Последние 4 услуги в 2 ряда по 2
    last_four = services_list[-4:]
    for i in range(0, 4, 2):
        row = []
        for j in range(2):
            if i + j < len(last_four):
                service_key, service_name = last_four[i + j]
                row.append(InlineKeyboardButton(service_name, callback_data=f"service_{service_key}"))
        keyboard.append(row)
    
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
    user_id = update.effective_user.id
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
    user_id = update.effective_user.id
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
        
        # Показываем выбор услуг
        await update.message.reply_text(
            f'💰 Сумма: {formatted_amount} CZK\n\n'
            '🌿 Выберите услугу для указания в платеже:\n'
            '👇 Нажмите на нужную услугу',
            reply_markup=get_services_keyboard()
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
        
        # Показываем выбор услуг
        await query.edit_message_text(
            f'💰 Сумма: {formatted_amount} CZK\n\n'
            '🌿 Выберите услугу для указания в платеже:\n'
            '👇 Нажмите на нужную услугу',
            reply_markup=get_services_keyboard()
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
    else:
        service_name = SERVICES.get(service_key)
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
    
    total_users = len(user_stats)
    total_requests = sum(user_stats.values())
    
    stats_text = f'📊 **СТАТИСТИКА БОТА**\n\n'
    stats_text += f'👥 Всего пользователей: {total_users}\n'
    stats_text += f'📱 Всего запросов: {total_requests}\n\n'
    
    if user_stats:
        stats_text += '**Топ пользователей:**\n'
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)
        for i, (uid, count) in enumerate(sorted_users[:5], 1):
            stats_text += f'{i}. User {uid}: {count} запросов\n'
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

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
    
    logger.info("Starting QR Payment Bot...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настройка keep-alive для предотвращения засыпания на Render
    if os.getenv('RENDER') and setup_render_keep_alive:
        try:
            # Запускаем keep-alive после создания application
            asyncio.create_task(setup_render_keep_alive())
            logger.info("✅ Render keep-alive activated")
        except Exception as e:
            logger.warning(f"⚠️ Keep-alive setup failed: {e}")
    elif os.getenv('RENDER'):
        logger.warning("⚠️ Running on Render but keep-alive module not available")
    
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
    
    # Запускаем бота
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
