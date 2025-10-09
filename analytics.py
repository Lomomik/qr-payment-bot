#!/usr/bin/env python3
"""
Расширенная аналитика для бота
Предоставляет детальные отчеты и графики
"""

from database import db
from datetime import datetime, timedelta
from typing import List, Dict


def format_daily_report() -> str:
    """Форматирует дневной отчет"""
    daily_stats = db.get_daily_stats(7)
    
    if not daily_stats:
        return "📊 Нет данных за последние 7 дней"
    
    report = "📊 **ДНЕВНАЯ СТАТИСТИКА (7 дней)**\n\n"
    
    for day in daily_stats:
        date = day['date']
        transactions = day['transactions']
        total = day['total_amount']
        avg = total / transactions if transactions > 0 else 0
        
        report += f"📅 {date}\n"
        report += f"  💰 Транзакций: {transactions}\n"
        report += f"  💵 Сумма: {total:,.0f} CZK\n"
        report += f"  📊 Средняя: {avg:.0f} CZK\n\n"
    
    return report


def format_services_report() -> str:
    """Форматирует отчет по услугам"""
    services = db.get_popular_services(10)
    
    if not services:
        return "📋 Нет данных по услугам"
    
    report = "🛍️ **ПОПУЛЯРНЫЕ УСЛУГИ**\n\n"
    
    total_count = sum(count for _, count in services)
    
    for i, (service, count) in enumerate(services, 1):
        percentage = (count / total_count * 100) if total_count > 0 else 0
        bar = "█" * int(percentage / 5)  # Простая визуализация
        report += f"{i}. {service}\n"
        report += f"   {bar} {count}x ({percentage:.1f}%)\n\n"
    
    return report


def format_users_report() -> str:
    """Форматирует отчет по пользователям"""
    users = db.get_all_users_stats()
    
    if not users:
        return "👥 Нет данных по пользователям"
    
    report = "👥 **АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ**\n\n"
    
    for i, user in enumerate(users[:10], 1):
        username = user['username'] or f"User{user['user_id']}"
        name = user['first_name'] or ""
        
        report += f"{i}. @{username}"
        if name:
            report += f" ({name})"
        report += "\n"
        report += f"   💰 {user['transactions_count']} транзакций\n"
        report += f"   💵 {user['total_amount']:.0f} CZK\n"
        report += f"   📅 Последний: {user['last_seen'][:10]}\n\n"
    
    return report


def format_summary_report() -> str:
    """Форматирует общий отчет"""
    stats = db.get_total_stats()
    recent = db.get_recent_transactions(5)
    
    report = "📊 **ОБЩАЯ АНАЛИТИКА**\n\n"
    report += f"👥 Пользователей: {stats['total_users']}\n"
    report += f"💰 Транзакций: {stats['total_transactions']}\n"
    report += f"💵 Общая сумма: {stats['total_amount']:,.0f} CZK\n"
    report += f"📊 Средний чек: {stats['avg_amount']:.0f} CZK\n"
    report += f"🟢 Активных (24ч): {stats['active_24h']}\n\n"
    
    if recent:
        report += "🕒 **ПОСЛЕДНИЕ ТРАНЗАКЦИИ:**\n\n"
        for t in recent:
            username = t['username'] or f"ID{t['user_id']}"
            service = t['service'] or "Без услуги"
            timestamp = t['timestamp'][:16].replace('T', ' ')
            report += f"• {timestamp} - @{username}\n"
            report += f"  {t['amount']:.0f} CZK - {service}\n\n"
    
    return report


if __name__ == '__main__':
    # Тестирование
    print("=" * 50)
    print(format_summary_report())
    print("=" * 50)
    print(format_daily_report())
    print("=" * 50)
    print(format_services_report())
    print("=" * 50)
    print(format_users_report())
