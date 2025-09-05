#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Admin Notification and Analytics System for QR Payment Bot
Система уведомлений администратора и аналитики для бота QR платежей
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
import json
import os

logger = logging.getLogger(__name__)

class AdminNotificationSystem:
    """Система уведомлений администратора"""
    
    def __init__(self, admin_id: int):
        self.admin_id = admin_id
        self.notification_settings = {
            'new_payments': True,
            'errors': True,
            'daily_summary': True,
            'user_milestones': True  # 10, 50, 100 пользователей и т.д.
        }
    
    async def notify_new_payment(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, 
                               username: str, amount: float, service: str):
        """Уведомление о новом платеже"""
        if not self.notification_settings['new_payments']:
            return
        
        try:
            message = f"""
💳 <b>Новый платеж создан</b>

👤 <b>Пользователь:</b> {username} (ID: {user_id})
💰 <b>Сумма:</b> {amount} Kč
🎯 <b>Услуга:</b> {service}
⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}

#payment #новый_платеж
"""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send payment notification: {e}")
    
    async def notify_new_user(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, 
                            username: str, total_users: int):
        """Уведомление о новом пользователе"""
        try:
            # Уведомляем о важных вехах
            milestones = [10, 25, 50, 100, 250, 500, 1000]
            if total_users in milestones:
                message = f"""
🎉 <b>Веха достигнута!</b>

👥 <b>Общее количество пользователей:</b> {total_users}
🆕 <b>Последний пользователь:</b> {username} (ID: {user_id})

#milestone #пользователи
"""
            else:
                message = f"""
👋 <b>Новый пользователь</b>

👤 {username} (ID: {user_id})
👥 <b>Всего пользователей:</b> {total_users}

#новый_пользователь
"""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send new user notification: {e}")
    
    async def notify_error(self, context: ContextTypes.DEFAULT_TYPE, error_type: str, 
                         error_message: str, user_id: int = None):
        """Уведомление об ошибке"""
        if not self.notification_settings['errors']:
            return
        
        try:
            message = f"""
🚨 <b>Ошибка в боте</b>

🔴 <b>Тип:</b> {error_type}
📝 <b>Сообщение:</b> {error_message}
👤 <b>Пользователь:</b> {user_id or 'Неизвестен'}
⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}

#error #ошибка
"""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    async def send_daily_summary(self, context: ContextTypes.DEFAULT_TYPE, stats: Dict):
        """Ежедневная сводка"""
        if not self.notification_settings['daily_summary']:
            return
        
        try:
            message = f"""
📊 <b>Ежедневная сводка</b>
📅 {datetime.now().strftime('%d.%m.%Y')}

💳 <b>Платежи за день:</b> {stats.get('daily_payments', 0)}
💰 <b>Сумма за день:</b> {stats.get('daily_amount', 0):.2f} Kč
👥 <b>Новые пользователи:</b> {stats.get('new_users', 0)}
📈 <b>Активные пользователи:</b> {stats.get('active_users', 0)}

<b>Топ услуги дня:</b>
{self._format_top_services(stats.get('top_services', {}))}

#daily_summary #статистика
"""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
    
    def _format_top_services(self, services: Dict) -> str:
        """Форматирует топ услуги"""
        if not services:
            return "Нет данных"
        
        formatted = []
        for service, count in sorted(services.items(), key=lambda x: x[1], reverse=True)[:5]:
            formatted.append(f"• {service}: {count}")
        
        return "\n".join(formatted) if formatted else "Нет данных"

class AdvancedAnalytics:
    """Расширенная система аналитики"""
    
    def __init__(self):
        self.data_file = "bot_analytics.json"
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Загружает данные аналитики"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")
        
        return {
            'users': {},
            'payments': [],
            'daily_stats': {},
            'service_stats': {},
            'error_log': []
        }
    
    def _save_data(self):
        """Сохраняет данные аналитики"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")
    
    def log_user_activity(self, user_id: int, username: str, action: str):
        """Логирует активность пользователя"""
        user_key = str(user_id)
        current_time = datetime.now().isoformat()
        
        if user_key not in self.data['users']:
            self.data['users'][user_key] = {
                'username': username,
                'first_seen': current_time,
                'last_seen': current_time,
                'total_actions': 0,
                'payments_created': 0
            }
        
        self.data['users'][user_key]['username'] = username  # Обновляем имя
        self.data['users'][user_key]['last_seen'] = current_time
        self.data['users'][user_key]['total_actions'] += 1
        
        if action == 'payment_created':
            self.data['users'][user_key]['payments_created'] += 1
        
        self._save_data()
    
    def log_payment(self, user_id: int, amount: float, service: str):
        """Логирует платеж"""
        payment_data = {
            'user_id': user_id,
            'amount': amount,
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        self.data['payments'].append(payment_data)
        
        # Обновляем статистику услуг
        if service in self.data['service_stats']:
            self.data['service_stats'][service] += 1
        else:
            self.data['service_stats'][service] = 1
        
        # Обновляем дневную статистику
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.data['daily_stats']:
            self.data['daily_stats'][today] = {
                'payments': 0,
                'amount': 0,
                'unique_users': set()
            }
        
        self.data['daily_stats'][today]['payments'] += 1
        self.data['daily_stats'][today]['amount'] += amount
        self.data['daily_stats'][today]['unique_users'].add(user_id)
        
        self._save_data()
    
    def get_user_stats(self) -> Dict:
        """Возвращает статистику пользователей"""
        total_users = len(self.data['users'])
        
        # Активные пользователи за последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)
        active_users = 0
        
        for user_data in self.data['users'].values():
            last_seen = datetime.fromisoformat(user_data['last_seen'])
            if last_seen >= week_ago:
                active_users += 1
        
        return {
            'total_users': total_users,
            'active_users_week': active_users,
            'new_users_today': self._count_new_users_today()
        }
    
    def get_payment_stats(self) -> Dict:
        """Возвращает статистику платежей"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Статистика за сегодня
        today_payments = [p for p in self.data['payments'] if p['date'] == today]
        today_amount = sum(p['amount'] for p in today_payments)
        
        # Общая статистика
        total_payments = len(self.data['payments'])
        total_amount = sum(p['amount'] for p in self.data['payments'])
        avg_payment = total_amount / max(total_payments, 1)
        
        return {
            'total_payments': total_payments,
            'total_amount': total_amount,
            'avg_payment': avg_payment,
            'today_payments': len(today_payments),
            'today_amount': today_amount
        }
    
    def get_service_stats(self) -> Dict:
        """Возвращает статистику услуг"""
        return dict(sorted(
            self.data['service_stats'].items(),
            key=lambda x: x[1],
            reverse=True
        ))
    
    def _count_new_users_today(self) -> int:
        """Считает новых пользователей за сегодня"""
        today = datetime.now().date()
        count = 0
        
        for user_data in self.data['users'].values():
            first_seen = datetime.fromisoformat(user_data['first_seen']).date()
            if first_seen == today:
                count += 1
        
        return count

# Команды администратора
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику администратору"""
    user_id = update.effective_user.id
    admin_id = int(os.getenv('ADMIN_TELEGRAM_ID', 0))
    
    if user_id != admin_id:
        await update.message.reply_text("❌ Доступ запрещен.")
        return
    
    analytics = context.bot_data.get('analytics')
    if not analytics:
        await update.message.reply_text("❌ Система аналитики не инициализирована.")
        return
    
    user_stats = analytics.get_user_stats()
    payment_stats = analytics.get_payment_stats()
    service_stats = analytics.get_service_stats()
    
    message = f"""
📊 <b>Статистика бота</b>

👥 <b>Пользователи:</b>
• Всего: {user_stats['total_users']}
• Активные (неделя): {user_stats['active_users_week']}
• Новые сегодня: {user_stats['new_users_today']}

💳 <b>Платежи:</b>
• Всего: {payment_stats['total_payments']}
• Общая сумма: {payment_stats['total_amount']:.2f} Kč
• Средний платеж: {payment_stats['avg_payment']:.2f} Kč
• Сегодня: {payment_stats['today_payments']} ({payment_stats['today_amount']:.2f} Kč)

🎯 <b>Топ услуги:</b>
"""
    
    for service, count in list(service_stats.items())[:5]:
        message += f"• {service}: {count}\n"
    
    keyboard = [
        [
            InlineKeyboardButton("📈 Детальная статистика", callback_data="admin_detailed_stats"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="admin_refresh_stats"),
            InlineKeyboardButton("📊 Экспорт", callback_data="admin_export_data")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback-запросов администратора"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    admin_id = int(os.getenv('ADMIN_TELEGRAM_ID', 0))
    
    if user_id != admin_id:
        await query.edit_message_text("❌ Доступ запрещен.")
        return
    
    if query.data == "admin_refresh_stats":
        # Перезагружаем статистику
        await admin_stats(update, context)
    
    elif query.data == "admin_detailed_stats":
        await show_detailed_stats(query, context)
    
    elif query.data == "admin_settings":
        await show_admin_settings(query, context)
    
    elif query.data == "admin_export_data":
        await export_analytics_data(query, context)

async def show_detailed_stats(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает детальную статистику"""
    analytics = context.bot_data.get('analytics')
    if not analytics:
        await query.edit_message_text("❌ Система аналитики не инициализирована.")
        return
    
    # Статистика за последние 7 дней
    week_stats = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_data = analytics.data['daily_stats'].get(date, {})
        payments = day_data.get('payments', 0)
        amount = day_data.get('amount', 0)
        week_stats.append(f"• {date}: {payments} платежей ({amount:.0f} Kč)")
    
    message = f"""
📈 <b>Детальная статистика</b>

📅 <b>Последние 7 дней:</b>
{chr(10).join(week_stats)}

🔄 <b>Активность пользователей:</b>
• Пользователи с 1+ платежом: {len([u for u in analytics.data['users'].values() if u['payments_created'] > 0])}
• Самые активные: {get_top_users(analytics.data['users'])}
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_refresh_stats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

def get_top_users(users_data: Dict) -> str:
    """Возвращает топ активных пользователей"""
    sorted_users = sorted(
        users_data.items(),
        key=lambda x: x[1]['total_actions'],
        reverse=True
    )[:3]
    
    result = []
    for user_id, data in sorted_users:
        username = data.get('username', 'Unknown')
        actions = data['total_actions']
        result.append(f"{username} ({actions})")
    
    return ", ".join(result) if result else "Нет данных"

async def show_admin_settings(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает настройки администратора"""
    message = """
⚙️ <b>Настройки администратора</b>

Выберите настройку для изменения:
"""
    
    keyboard = [
        [InlineKeyboardButton("🔔 Уведомления о платежах", callback_data="toggle_payment_notifications")],
        [InlineKeyboardButton("🚨 Уведомления об ошибках", callback_data="toggle_error_notifications")],
        [InlineKeyboardButton("📊 Ежедневная сводка", callback_data="toggle_daily_summary")],
        [InlineKeyboardButton("🎯 Уведомления о вехах", callback_data="toggle_milestone_notifications")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_refresh_stats")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def export_analytics_data(query, context: ContextTypes.DEFAULT_TYPE):
    """Экспортирует данные аналитики"""
    analytics = context.bot_data.get('analytics')
    if not analytics:
        await query.edit_message_text("❌ Система аналитики не инициализирована.")
        return
    
    try:
        # Создаем CSV с данными о платежах
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Дата', 'Пользователь', 'Сумма', 'Услуга'])
        
        for payment in analytics.data['payments']:
            writer.writerow([
                payment['timestamp'],
                payment['user_id'],
                payment['amount'],
                payment['service']
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        # Отправляем файл
        from io import BytesIO
        file_buffer = BytesIO(csv_content.encode('utf-8'))
        file_buffer.name = f"analytics_{datetime.now().strftime('%Y%m%d')}.csv"
        
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_buffer,
            filename=f"analytics_{datetime.now().strftime('%Y%m%d')}.csv",
            caption="📊 Данные аналитики экспортированы"
        )
        
        await query.edit_message_text("✅ Данные экспортированы и отправлены файлом.")
        
    except Exception as e:
        logger.error(f"Failed to export analytics data: {e}")
        await query.edit_message_text("❌ Ошибка при экспорте данных.")

# Функция для настройки системы в основном боте
def setup_admin_system(application, admin_id: int):
    """Настраивает систему администратора"""
    # Инициализируем системы
    admin_notifications = AdminNotificationSystem(admin_id)
    analytics = AdvancedAnalytics()
    
    # Сохраняем в bot_data
    application.bot_data['admin_notifications'] = admin_notifications
    application.bot_data['analytics'] = analytics
    
    # Добавляем обработчики команд администратора
    application.add_handler(CommandHandler('admin', admin_stats))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^admin_'))
    
    # Настраиваем ежедневную отправку сводки
    from telegram.ext import JobQueue
    job_queue = application.job_queue
    
    # Отправляем сводку каждый день в 23:00
    job_queue.run_daily(
        send_daily_summary_job,
        time=datetime.strptime('23:00', '%H:%M').time(),
        name='daily_summary'
    )

async def send_daily_summary_job(context: ContextTypes.DEFAULT_TYPE):
    """Задача для отправки ежедневной сводки"""
    try:
        admin_notifications = context.bot_data.get('admin_notifications')
        analytics = context.bot_data.get('analytics')
        
        if admin_notifications and analytics:
            today = datetime.now().strftime('%Y-%m-%d')
            daily_data = analytics.data['daily_stats'].get(today, {})
            
            stats = {
                'daily_payments': daily_data.get('payments', 0),
                'daily_amount': daily_data.get('amount', 0),
                'new_users': analytics._count_new_users_today(),
                'active_users': len(daily_data.get('unique_users', set())),
                'top_services': analytics.get_service_stats()
            }
            
            await admin_notifications.send_daily_summary(context, stats)
    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}")
