#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Error Handler and Validation System for QR Payment Bot
Система обработки ошибок и валидации для бота QR платежей
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, NetworkError, BadRequest, TimedOut
from functools import wraps
import traceback

logger = logging.getLogger(__name__)

class PaymentValidationError(Exception):
    """Кастомное исключение для ошибок валидации платежей"""
    pass

def error_handler(func):
    """Декоратор для обработки ошибок в хендлерах"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except PaymentValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            await send_user_error(update, f"❌ {str(e)}")
        except (NetworkError, TimedOut) as e:
            logger.error(f"Network error in {func.__name__}: {e}")
            await send_user_error(update, "🌐 Проблемы с сетью. Попробуйте позже.")
        except BadRequest as e:
            logger.error(f"Bad request in {func.__name__}: {e}")
            await send_user_error(update, "❌ Неверный запрос. Попробуйте /start")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}\n{traceback.format_exc()}")
            await send_user_error(update, "❌ Произошла ошибка. Администратор уведомлен.")
            # Уведомляем администратора
            await notify_admin(context, f"Error in {func.__name__}: {str(e)}")
    return wrapper

async def send_user_error(update: Update, message: str):
    """Отправляет сообщение об ошибке пользователю"""
    try:
        if update.callback_query:
            await update.callback_query.answer(text="Произошла ошибка", show_alert=True)
            await update.callback_query.message.reply_text(f"{message}\n\nИспользуйте /start для начала.")
        elif update.message:
            await update.message.reply_text(f"{message}\n\nИспользуйте /start для начала.")
    except Exception as e:
        logger.error(f"Failed to send error message to user: {e}")

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Уведомляет администратора об ошибке"""
    try:
        admin_id = context.bot_data.get('admin_id')
        if admin_id:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🚨 <b>Ошибка в боте:</b>\n\n{message}",
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

def validate_amount(amount_str: str) -> float:
    """Валидирует сумму платежа"""
    try:
        # Очищаем от лишних символов
        clean_amount = amount_str.replace(',', '.').replace(' ', '').replace('Kč', '').replace('kč', '')
        amount = float(clean_amount)
        
        if amount <= 0:
            raise PaymentValidationError("Сумма должна быть больше 0")
        
        if amount > 1000000:
            raise PaymentValidationError("Максимальная сумма: 1,000,000 Kč")
        
        # Проверяем на разумные десятичные места
        if len(str(amount).split('.')[-1]) > 2:
            raise PaymentValidationError("Максимум 2 знака после запятой")
        
        return amount
        
    except ValueError:
        raise PaymentValidationError("Неверный формат суммы. Используйте числа (например: 1250 или 1250.50)")

def validate_service_key(service_key: str, available_services: dict) -> str:
    """Валидирует ключ услуги"""
    if service_key not in available_services and service_key != "none":
        raise PaymentValidationError("Неизвестная услуга")
    return service_key

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок"""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Извлекаем информацию об ошибке
    error_message = str(context.error)
    error_type = type(context.error).__name__
    
    # Определяем тип ошибки и реагируем соответственно
    if isinstance(context.error, NetworkError):
        user_message = "🌐 Проблемы с сетью. Попробуйте позже."
    elif isinstance(context.error, BadRequest):
        user_message = "❌ Неверный запрос. Попробуйте /start"
    elif isinstance(context.error, TimedOut):
        user_message = "⏰ Превышено время ожидания. Попробуйте еще раз."
    else:
        user_message = "❌ Произошла неожиданная ошибка. Администратор уведомлен."
    
    # Отправляем сообщение пользователю
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=user_message + "\n\nИспользуйте /start для начала."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")
    
    # Уведомляем администратора о критических ошибках
    if not isinstance(context.error, (NetworkError, TimedOut)):
        admin_message = f"""
🚨 <b>Критическая ошибка в боте</b>

<b>Тип:</b> {error_type}
<b>Сообщение:</b> {error_message}
<b>Пользователь:</b> {update.effective_user.id if isinstance(update, Update) and update.effective_user else 'Unknown'}
<b>Чат:</b> {update.effective_chat.id if isinstance(update, Update) and update.effective_chat else 'Unknown'}

<b>Трассировка:</b>
<code>{traceback.format_exc()}</code>
"""
        await notify_admin(context, admin_message)

# Функции для мониторинга и аналитики
class BotAnalytics:
    """Класс для сбора аналитики бота"""
    
    def __init__(self):
        self.stats = {
            'total_users': set(),
            'total_payments': 0,
            'total_amount': 0,
            'service_popularity': {},
            'error_count': 0,
            'daily_stats': {}
        }
    
    def log_user(self, user_id: int):
        """Регистрирует нового пользователя"""
        self.stats['total_users'].add(user_id)
    
    def log_payment(self, amount: float, service: str):
        """Регистрирует платеж"""
        self.stats['total_payments'] += 1
        self.stats['total_amount'] += amount
        
        if service in self.stats['service_popularity']:
            self.stats['service_popularity'][service] += 1
        else:
            self.stats['service_popularity'][service] = 1
    
    def log_error(self):
        """Регистрирует ошибку"""
        self.stats['error_count'] += 1
    
    def get_stats_summary(self) -> str:
        """Возвращает сводку статистики"""
        total_users = len(self.stats['total_users'])
        avg_payment = self.stats['total_amount'] / max(self.stats['total_payments'], 1)
        
        popular_services = sorted(
            self.stats['service_popularity'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        summary = f"""
📊 <b>Статистика бота</b>

👥 <b>Пользователи:</b> {total_users}
💳 <b>Платежи:</b> {self.stats['total_payments']}
💰 <b>Общая сумма:</b> {self.stats['total_amount']:.2f} Kč
📈 <b>Средний платеж:</b> {avg_payment:.2f} Kč
❌ <b>Ошибки:</b> {self.stats['error_count']}

<b>Популярные услуги:</b>
"""
        
        for service, count in popular_services:
            summary += f"• {service}: {count}\n"
        
        return summary

# Глобальный экземпляр аналитики
analytics = BotAnalytics()

# Система лимитов и защиты от спама
class RateLimiter:
    """Система ограничения частоты запросов"""
    
    def __init__(self):
        self.user_requests = {}
        self.max_requests_per_minute = 10
    
    def is_allowed(self, user_id: int) -> bool:
        """Проверяет, разрешен ли запрос пользователя"""
        import time
        current_time = time.time()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Удаляем старые запросы (старше минуты)
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < 60
        ]
        
        # Проверяем лимит
        if len(self.user_requests[user_id]) >= self.max_requests_per_minute:
            return False
        
        # Добавляем текущий запрос
        self.user_requests[user_id].append(current_time)
        return True

rate_limiter = RateLimiter()

def rate_limit(func):
    """Декоратор для ограничения частоты запросов"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text(
                "⚠️ Слишком много запросов. Подождите минуту перед следующим действием."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper
