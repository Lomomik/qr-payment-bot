#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced QR Payment Bot with ConversationHandler
Улучшенная версия бота с использованием ConversationHandler для надежного управления состояниями
"""

import logging
import os
import qrcode
from io import BytesIO
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', 0))
OWNER_NAME = os.getenv('OWNER_NAME', 'ВЛАДЕЛЕЦ')
ACCOUNT_NUMBER = os.getenv('ACCOUNT_NUMBER', '1234567890/1234')

# Состояния ConversationHandler
SELECTING_AMOUNT, SELECTING_SERVICE, CONFIRMING_PAYMENT = range(3)

# Услуги с эмодзи-категоризацией
SERVICES = {
    'brow_correction': '🌿 ÚPRAVA OBOČÍ',
    'brow_coloring': '🌿 BARVENÍ OBOČÍ',
    'brow_lamination': '🌿 LAMINACE OBOČÍ',
    'brow_styling': '🌿 STYLING OBOČÍ',
    'lash_lamination': '👁️ LAMINACE ŘAS',
    'lash_coloring': '👁️ BARVENÍ ŘAS',
    'lash_extension': '👁️ PRODLUŽOVÁNÍ ŘAS',
    'combo_lash_brow': '✨ LAMINACE ŘAS + OBOČÍ',
    'combo_full': '✨ KOMPLEXNÍ PÉČE',
    'makeup': '👄 LÍČENÍ',
    'hairstyle': '👄 ÚČES',
    'consultation': '💬 KONZULTACE'
}

def format_amount_czech(amount):
    """Форматирует сумму в чешском формате (запятая как десятичный разделитель)"""
    try:
        decimal_amount = Decimal(str(amount))
        return f"{decimal_amount:.2f}".replace('.', ',')
    except (InvalidOperation, ValueError):
        return "0,00"

def generate_qr_code(amount, service_name):
    """Генерирует QR-код для чешского банковского платежа в формате SPD"""
    iban = f"CZ{ACCOUNT_NUMBER.replace('/', '')}"
    formatted_amount = format_amount_czech(amount)
    
    # Стандартный формат SPD для чешских банков
    qr_data = f"SPD*1.0*ACC:{iban}*RN:{OWNER_NAME.upper()}*AM:{formatted_amount}*CC:CZK*MSG:{service_name}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    return bio

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начальная команда - переход к выбору суммы"""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.first_name}) started the bot")
    
    welcome_text = f"""
🌸 <b>Добро пожаловать в салон красоты Noéme!</b> 🌸

Привет, {user.first_name}! 
Этот бот поможет вам создать QR-код для оплаты услуг.

Выберите сумму оплаты:
"""
    
    # Создаем клавиатуру с суммами
    keyboard = [
        [
            InlineKeyboardButton("500 Kč", callback_data="amount_500"),
            InlineKeyboardButton("700 Kč", callback_data="amount_700"),
            InlineKeyboardButton("900 Kč", callback_data="amount_900")
        ],
        [
            InlineKeyboardButton("1100 Kč", callback_data="amount_1100"),
            InlineKeyboardButton("1300 Kč", callback_data="amount_1300"),
            InlineKeyboardButton("1500 Kč", callback_data="amount_1500")
        ],
        [
            InlineKeyboardButton("1700 Kč", callback_data="amount_1700"),
            InlineKeyboardButton("1800 Kč", callback_data="amount_1800"),
        ],
        [InlineKeyboardButton("✏️ Ввести свою сумму", callback_data="amount_custom")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    return SELECTING_AMOUNT

async def handle_amount_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора суммы"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "amount_custom":
        await query.edit_message_text(
            "💰 Введите сумму в чешских кронах (например: 1250)\n\n"
            "Минимум: 1 Kč, Максимум: 1,000,000 Kč",
            parse_mode=ParseMode.HTML
        )
        return SELECTING_AMOUNT  # Остаемся в том же состоянии для ввода суммы
    
    # Извлекаем сумму из callback_data
    amount = int(query.data.split('_')[1])
    context.user_data['amount'] = amount
    
    logger.info(f"User {query.from_user.id} selected amount: {amount} Kč")
    
    return await show_service_selection(update, context)

async def handle_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода пользовательской суммы"""
    try:
        amount = float(update.message.text.replace(',', '.'))
        
        if amount <= 0:
            await update.message.reply_text(
                "❌ Сумма должна быть больше 0. Попробуйте еще раз:",
                parse_mode=ParseMode.HTML
            )
            return SELECTING_AMOUNT
        
        if amount > 1000000:
            await update.message.reply_text(
                "❌ Максимальная сумма: 1,000,000 Kč. Попробуйте еще раз:",
                parse_mode=ParseMode.HTML
            )
            return SELECTING_AMOUNT
        
        context.user_data['amount'] = amount
        logger.info(f"User {update.effective_user.id} entered custom amount: {amount} Kč")
        
        return await show_service_selection(update, context)
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат суммы. Введите число (например: 1250 или 1250.50):",
            parse_mode=ParseMode.HTML
        )
        return SELECTING_AMOUNT

async def show_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает выбор услуг"""
    amount = context.user_data.get('amount')
    
    text = f"""
💰 <b>Сумма: {amount} Kč</b>

Теперь выберите услугу:
"""
    
    # Создаем клавиатуру с услугами
    services_list = list(SERVICES.items())
    keyboard = []
    
    # Первые услуги по одной в ряд
    for i in range(0, min(8, len(services_list))):
        service_key, service_name = services_list[i]
        keyboard.append([InlineKeyboardButton(service_name, callback_data=f"service_{service_key}")])
    
    # Последние 4 услуги в виде сетки 2x2
    if len(services_list) > 8:
        remaining_services = services_list[8:]
        for i in range(0, len(remaining_services), 2):
            row = []
            for j in range(2):
                if i + j < len(remaining_services):
                    service_key, service_name = remaining_services[i + j]
                    # Укороченное название для кнопок
                    short_name = service_name.split(' ', 1)[1] if ' ' in service_name else service_name
                    row.append(InlineKeyboardButton(short_name, callback_data=f"service_{service_key}"))
            if row:
                keyboard.append(row)
    
    # Добавляем опцию "без указания услуги"
    keyboard.append([InlineKeyboardButton("🎯 Без указания услуги", callback_data="service_none")])
    keyboard.append([InlineKeyboardButton("◀️ Назад к выбору суммы", callback_data="back_to_amount")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    return SELECTING_SERVICE

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора услуги"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_amount":
        return await start(update, context)
    
    service_key = query.data.split('_', 1)[1]
    
    if service_key == "none":
        service_name = "Оплата услуг салона"
        display_service = "Без указания конкретной услуги"
    else:
        service_name = SERVICES.get(service_key, "Неизвестная услуга")
        display_service = service_name
    
    context.user_data['service'] = service_name
    context.user_data['service_display'] = display_service
    
    logger.info(f"User {query.from_user.id} selected service: {service_name}")
    
    return await show_payment_confirmation(update, context)

async def show_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает подтверждение платежа"""
    amount = context.user_data.get('amount')
    service_display = context.user_data.get('service_display')
    
    text = f"""
📋 <b>Подтверждение платежа</b>

💰 <b>Сумма:</b> {amount} Kč
🎯 <b>Услуга:</b> {service_display}
🏦 <b>Получатель:</b> {OWNER_NAME}

Все верно? Создать QR-код для оплаты?
"""
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Создать QR-код", callback_data="confirm_payment"),
            InlineKeyboardButton("❌ Отменить", callback_data="cancel_payment")
        ],
        [InlineKeyboardButton("◀️ Изменить услугу", callback_data="back_to_service")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    return CONFIRMING_PAYMENT

async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка подтверждения платежа"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_payment":
        await query.edit_message_text(
            "❌ Создание QR-кода отменено.\n\nИспользуйте /start для создания нового платежа.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    if query.data == "back_to_service":
        return await show_service_selection(update, context)
    
    if query.data == "confirm_payment":
        amount = context.user_data.get('amount')
        service_name = context.user_data.get('service')
        
        try:
            # Генерируем QR-код
            qr_image = generate_qr_code(amount, service_name)
            
            caption = f"""
✅ <b>QR-код создан!</b>

💰 <b>Сумма:</b> {amount} Kč
🎯 <b>Услуга:</b> {context.user_data.get('service_display')}
🏦 <b>Получатель:</b> {OWNER_NAME}

📱 <b>Для оплаты:</b>
1. Откройте банковское приложение
2. Отсканируйте QR-код
3. Подтвердите платеж

🏪 <b>Поддерживаемые банки:</b> Air Bank, Raiffeisenbank CZ
"""
            
            await query.edit_message_text("⏳ Генерируем QR-код...")
            
            # Отправляем QR-код
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=qr_image,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
            # Добавляем основное меню
            main_menu = ReplyKeyboardMarkup([
                [KeyboardButton("💳 Новый платеж")],
                [KeyboardButton("ℹ️ Информация"), KeyboardButton("👤 Контакты")]
            ], resize_keyboard=True, one_time_keyboard=False)
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Используйте меню ниже для дальнейших действий:",
                reply_markup=main_menu
            )
            
            logger.info(f"QR code generated for user {query.from_user.id}: {amount} Kč, {service_name}")
            
            # Очищаем данные пользователя
            context.user_data.clear()
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            await query.edit_message_text(
                "❌ Ошибка при создании QR-кода. Попробуйте еще раз.\n\n"
                "Используйте /start для создания нового платежа.",
                parse_mode=ParseMode.HTML
            )
        
        return ConversationHandler.END

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка основного меню"""
    text = update.message.text
    
    if text == "💳 Новый платеж":
        return await start(update, context)
    
    elif text == "ℹ️ Информация":
        info_text = """
🌸 <b>Салон красоты Noéme</b> 🌸

🎯 <b>Наши услуги:</b>
🌿 Уход за бровями (коррекция, окрашивание, ламинирование)
👁️ Уход за ресницами (ламинирование, окрашивание, наращивание)
✨ Комплексные процедуры
👄 Макияж и прически

💳 <b>Оплата:</b>
Поддерживаются все чешские банки с QR-платежами
Безопасная оплата через банковское приложение

🏪 <b>Режим работы:</b>
Пн-Пт: 9:00-19:00
Сб: 9:00-17:00
Вс: по записи
"""
        await update.message.reply_text(info_text, parse_mode=ParseMode.HTML)
    
    elif text == "👤 Контакты":
        contact_text = f"""
📞 <b>Контакты салона Noéme</b>

👩‍💼 <b>Администратор:</b> {OWNER_NAME}
📱 <b>Телефон:</b> +420 XXX XXX XXX
📧 <b>Email:</b> info@noeme.cz
🌐 <b>Сайт:</b> www.noeme.cz

📍 <b>Адрес:</b>
Адрес салона
Praha, Czech Republic

📅 <b>Запись:</b>
Онлайн на сайте или по телефону
"""
        await update.message.reply_text(contact_text, parse_mode=ParseMode.HTML)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции"""
    await update.message.reply_text(
        "❌ Операция отменена.\n\nИспользуйте /start для создания нового платежа.",
        parse_mode=ParseMode.HTML
    )
    context.user_data.clear()
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда помощи"""
    help_text = """
🆘 <b>Помощь по использованию бота</b>

<b>Команды:</b>
/start - Создать новый QR-код для оплаты
/help - Показать эту справку
/cancel - Отменить текущую операцию

<b>Как пользоваться:</b>
1. Нажмите /start
2. Выберите сумму оплаты
3. Выберите услугу
4. Подтвердите данные
5. Получите QR-код для оплаты

<b>Поддержка:</b>
Если у вас возникли проблемы, обратитесь к администратору салона.
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

def main() -> None:
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex("💳 Новый платеж"), start)
        ],
        states={
            SELECTING_AMOUNT: [
                CallbackQueryHandler(handle_amount_selection, pattern="^amount_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_amount)
            ],
            SELECTING_SERVICE: [
                CallbackQueryHandler(handle_service_selection, pattern="^(service_|back_to_)")
            ],
            CONFIRMING_PAYMENT: [
                CallbackQueryHandler(handle_payment_confirmation, pattern="^(confirm_|cancel_|back_to_)")
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)
        ],
        persistent=True,
        name='payment_conversation'
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.Regex("ℹ️ Информация|👤 Контакты"), handle_main_menu))
    
    # Запускаем бота
    logger.info("Starting Enhanced QR Payment Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
