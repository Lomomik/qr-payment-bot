#!/usr/bin/env python3
"""
ПРОСТАЯ тестовая версия бота без Google Calendar
Для проверки основной функциональности
"""

import os
import logging
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

# Загружаем ТЕСТОВЫЕ переменные окружения
load_dotenv('.env.test')

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID')
OWNER_NAME = os.getenv('OWNER_NAME', 'ULIANA EMELINA (TEST)')
ACCOUNT_NUMBER = os.getenv('ACCOUNT_NUMBER', '3247217010/3030')
IBAN = 'CZ3230300000003247217010'

# Статистика
user_stats = {}

# Тестовые события календаря (имитация Google Calendar)
MOCK_CALENDAR_EVENTS = [
    {
        'time': '09:00',
        'procedure': 'laminace řas + úprava obočí',
        'client': 'Anna',
        'price': 2200
    },
    {
        'time': '11:00', 
        'procedure': 'zesvětlení s úpravou a tonováním',
        'client': 'Marie',
        'price': 1600
    },
    {
        'time': '14:00',
        'procedure': 'líčení & účes',
        'client': 'Petra', 
        'price': 2000
    },
    {
        'time': '16:30',
        'procedure': 'laminace řas',
        'client': 'Elena',
        'price': 1500
    }
]

# Услуги салона
SERVICES = {
    'uprava_barveni': '🌿 ÚPRAVA A BARVENÍ',
    'uprava': '🌿 ÚPRAVA',
    'laminace_ras': '👁️ LAMINACE ŘAS',
    'barveni_ras': '👁️ BARVENÍ ŘAS',
    'liceni_uces': '👄 LÍČENÍ & ÚČES',
    'liceni': '👄 LÍČENÍ',
}

def get_main_keyboard():
    """Создает главное меню с кнопками"""
    keyboard = [
        [KeyboardButton('💰 Создать QR-код для оплаты')],
        [KeyboardButton('ℹ️ Реквизиты счета'), KeyboardButton('❓ Помощь')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_calendar_events_keyboard():
    """Создает клавиатуру с тестовыми календарными событиями"""
    keyboard = []
    
    # Добавляем события из тестового календаря
    for event in MOCK_CALENDAR_EVENTS:
        display_text = f"🕐 {event['time']} | {event['procedure'].title()} | {event['client']} - {event['price']} CZK"
        callback_data = f"calendar_{event['price']}_{event['procedure']}"
        keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
    
    # Разделитель
    keyboard.append([InlineKeyboardButton("➖➖➖ Другие варианты ➖➖➖", callback_data="separator")])
    
    # Стандартные кнопки
    keyboard.append([InlineKeyboardButton("💰 Выбрать сумму вручную", callback_data="manual_amount")])
    keyboard.append([InlineKeyboardButton("🛍️ Выбрать услугу и сумму", callback_data="manual_service")])
    
    return InlineKeyboardMarkup(keyboard)

def get_amount_keyboard():
    """Создает клавиатуру с быстрым выбором суммы"""
    keyboard = []
    amounts = range(500, 1900, 100)
    
    # Размещаем кнопки по 3 в ряд
    row = []
    for amount in amounts:
        row.append(InlineKeyboardButton(f"{amount} CZK", callback_data=f"amount_{amount}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("✏️ Ввести свою сумму", callback_data="amount_custom")])
    
    return InlineKeyboardMarkup(keyboard)

def get_services_keyboard():
    """Создает клавиатуру с выбором услуг"""
    keyboard = []
    
    for service_key, service_name in SERVICES.items():
        keyboard.append([InlineKeyboardButton(service_name, callback_data=f"service_{service_key}")])
    
    keyboard.append([InlineKeyboardButton("❌ Без указания услуги", callback_data="service_none")])
    
    return InlineKeyboardMarkup(keyboard)

def generate_qr_code(amount: float, service_msg: str = None) -> BytesIO:
    """Генерирует QR-код с данными для оплаты"""
    if amount == int(amount):
        formatted_amount = str(int(amount))
    else:
        formatted_amount = f"{amount:.2f}".replace('.', ',')
    
    qr_text = f"SPD*1.0*ACC:{IBAN}*RN:{OWNER_NAME.upper()}*AM:{formatted_amount}*CC:CZK"
    
    if service_msg:
        qr_text += f"*MSG:{service_msg}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    return bio

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    user_stats[user_id] = user_stats.get(user_id, 0) + 1
    
    await update.message.reply_text(
        '🧪 **ТЕСТОВАЯ ВЕРСИЯ БОТА С КАЛЕНДАРЕМ** 🧪\n'
        '👄 Добро пожаловать в систему оплаты салона красоты Noéme!\n\n'
        '💰 Этот бот поможет вам быстро создать QR-код для оплаты услуг.\n'
        '📅 Новинка: интеграция с календарем встреч!\n\n'
        '📱 Как это работает:\n'
        '• Выберите встречу из календаря или создайте QR-код вручную\n'
        '• Клиент сканирует QR-код своим банковским приложением\n'
        '• Автоматически заполняются все данные для перевода\n\n'
        '👇 Выберите действие с помощью кнопок ниже:',
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для создания QR-кода для оплаты"""
    user_id = update.effective_user.id
    user_stats[user_id] = user_stats.get(user_id, 0) + 1
    
    await update.message.reply_text(
        '🌿 <b>Создание QR-кода для оплаты</b>\n\n'
        '📅 <b>Сегодняшние встречи:</b>\n'
        'Выберите встречу для быстрого создания QR-кода\n'
        'или используйте ручной ввод\n\n'
        '👇 <b>Выберите вариант:</b>',
        reply_markup=get_calendar_events_keyboard(),
        parse_mode='HTML'
    )
    
    context.user_data['waiting_for_payment_option'] = True

async def handle_calendar_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора календарного события"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get('waiting_for_payment_option'):
        await query.edit_message_text('❌ Ошибка: неожиданный выбор события.')
        return
    
    try:
        parts = query.data.split('_', 2)
        if len(parts) != 3:
            raise ValueError("Invalid callback data format")
        
        _, price_str, procedure = parts
        amount = float(price_str)
        
        service_msg = procedure.upper()
        qr_image = generate_qr_code(amount, service_msg)
        
        formatted_amount = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        
        await query.delete_message()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=qr_image,
            caption=f'🌿 QR-код для оплаты услуг салона 🧪\n\n'
                   f'📅 <b>Из календаря:</b> {procedure.title()}\n'
                   f'💰 <b>Сумма:</b> {formatted_amount} CZK\n'
                   f'👤 <b>Получатель:</b> {OWNER_NAME}\n'
                   f'🏦 <b>Счет:</b> {ACCOUNT_NUMBER}\n\n'
                   f'📱 Покажите этот QR-код клиенту\n'
                   f'✅ Клиент сканирует код в своем банковском приложении\n\n'
                   f'🧪 <b>ТЕСТОВАЯ ВЕРСИЯ</b> - имитация календаря!',
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
        
        context.user_data['waiting_for_payment_option'] = False
        
        logger.info(f"TEST BOT: Calendar QR code generated for procedure: {procedure}, amount: {amount} CZK, user: {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error processing calendar selection: {e}")
        await query.edit_message_text('❌ Ошибка обработки выбора события.')

async def handle_payment_option_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора опции оплаты"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get('waiting_for_payment_option'):
        await query.edit_message_text('❌ Ошибка: неожиданный выбор опции.')
        return
    
    if query.data == 'separator':
        return
    elif query.data == 'manual_amount':
        context.user_data['waiting_for_payment_option'] = False
        context.user_data['waiting_for_amount'] = True
        
        await query.edit_message_text(
            '💰 <b>Выбор суммы</b>\n\n'
            '👇 Выберите сумму из списка или введите свою:',
            reply_markup=get_amount_keyboard(),
            parse_mode='HTML'
        )
    elif query.data == 'manual_service':
        context.user_data['waiting_for_payment_option'] = False
        context.user_data['waiting_for_service'] = True
        
        await query.edit_message_text(
            '🛍️ <b>Выбор услуги</b>\n\n'
            '👇 Выберите услугу для создания QR-кода:',
            reply_markup=get_services_keyboard(),
            parse_mode='HTML'
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    if text == '💰 Создать QR-код для оплаты':
        await payment_command(update, context)
        return
    elif text == 'ℹ️ Реквизиты счета':
        await update.message.reply_text(
            f'📋 **РЕКВИЗИТЫ СЧЕТА САЛОНА (ТЕСТ)**\n\n'
            f'👤 **Получатель:** {OWNER_NAME}\n'
            f'🏦 **Номер счета:** {ACCOUNT_NUMBER}\n'
            f'🌍 **IBAN:** {IBAN}\n'
            f'💱 **Валюта:** CZK (чешские кроны)\n\n'
            f'💰 Для создания QR-кода нажмите соответствующую кнопку ниже',
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    elif text == '❓ Помощь':
        await update.message.reply_text(
            '📋 **ИНСТРУКЦИЯ ДЛЯ СОТРУДНИКА (ТЕСТ)**\n\n'
            '**Как создать QR-код:**\n'
            '1️⃣ Нажмите кнопку "💰 Создать QR-код для оплаты"\n'
            '2️⃣ Выберите встречу из календаря или создайте вручную\n'
            '3️⃣ Покажите QR-код клиенту\n'
            '4️⃣ Клиент сканирует код в своем банковском приложении\n\n'
            '💡 QR-код автоматически заполнит все данные для перевода!\n\n'
            '🧪 **ТЕСТИРУЕМ ИНТЕГРАЦИЮ С КАЛЕНДАРЕМ**',
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    # Обработка ввода суммы
    if context.user_data.get('waiting_for_amount'):
        try:
            amount_text = update.message.text.strip().replace(',', '.')
            amount = float(amount_text)
            
            if amount <= 0 or amount > 1000000:
                await update.message.reply_text('❌ Неверная сумма! Введите от 1 до 1,000,000 CZK')
                return
            
            context.user_data['amount'] = amount
            context.user_data['waiting_for_amount'] = False
            context.user_data['waiting_for_service'] = True
            
            formatted_amount = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
            
            await update.message.reply_text(
                f'💰 Сумма: {formatted_amount} CZK\n\n'
                '🌿 Выберите услугу для указания в платеже:',
                reply_markup=get_services_keyboard(),
                parse_mode='HTML'
            )
            
        except ValueError:
            await update.message.reply_text('❌ Неверный формат суммы! Используйте числа: 500, 1000.50')
    else:
        await update.message.reply_text(
            '❓ Используйте кнопки для навигации\n\n'
            '🧪 **Тестовая версия с календарем**',
            reply_markup=get_main_keyboard()
        )

def main():
    """Главная функция"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found!")
        print("❌ Ошибка: BOT_TOKEN не найден в .env.test")
        return
    
    print("🧪 Запускаем ПРОСТУЮ тестовую версию бота...")
    print(f"🤖 Бот: {BOT_TOKEN[:10]}...")
    print(f"👤 Владелец: {OWNER_NAME}")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_calendar_selection, pattern=r'^calendar_'))
    application.add_handler(CallbackQueryHandler(handle_payment_option_selection, pattern=r'^(manual_amount|manual_service|separator)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    logger.info("Starting SIMPLE test bot...")
    print("✅ Простой тестовый бот запущен! Проверяйте календарные функции...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
