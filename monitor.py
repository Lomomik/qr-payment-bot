#!/usr/bin/env python3
"""
Скрипт мониторинга ресурсов для Oracle Cloud Always Free
Проверяет использование CPU, памяти, диска и статус бота
"""

import psutil
import subprocess
import json
from datetime import datetime

def get_system_info():
    """Получение информации о системе"""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Память
    memory = psutil.virtual_memory()
    memory_total = memory.total / (1024**3)  # В ГБ
    memory_used = memory.used / (1024**3)
    memory_percent = memory.percent
    
    # Диск
    disk = psutil.disk_usage('/')
    disk_total = disk.total / (1024**3)  # В ГБ
    disk_used = disk.used / (1024**3)
    disk_percent = (disk.used / disk.total) * 100
    
    # Сеть
    network = psutil.net_io_counters()
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cpu': {
            'percent': cpu_percent,
            'cores': cpu_count
        },
        'memory': {
            'total_gb': round(memory_total, 2),
            'used_gb': round(memory_used, 2),
            'percent': memory_percent
        },
        'disk': {
            'total_gb': round(disk_total, 2),
            'used_gb': round(disk_used, 2),
            'percent': round(disk_percent, 2)
        },
        'network': {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv
        }
    }

def get_bot_status():
    """Проверка статуса Telegram бота"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'telegram-bot'],
            capture_output=True,
            text=True
        )
        is_active = result.stdout.strip() == 'active'
        
        # Получение времени работы
        result = subprocess.run(
            ['systemctl', 'show', 'telegram-bot', '--property=ActiveEnterTimestamp'],
            capture_output=True,
            text=True
        )
        start_time = result.stdout.strip().split('=')[1] if '=' in result.stdout else 'Unknown'
        
        return {
            'status': 'running' if is_active else 'stopped',
            'start_time': start_time
        }
    except Exception as e:
        return {
            'status': 'unknown',
            'error': str(e)
        }

def format_bytes(bytes_value):
    """Форматирование байтов в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def print_status():
    """Вывод статуса в консоль"""
    system_info = get_system_info()
    bot_status = get_bot_status()
    
    print("=" * 60)
    print(f"📊 МОНИТОРИНГ ORACLE CLOUD СЕРВЕРА")
    print(f"🕐 Время: {system_info['timestamp']}")
    print("=" * 60)
    
    # Статус бота
    status_emoji = "🟢" if bot_status['status'] == 'running' else "🔴"
    print(f"🤖 Telegram бот: {status_emoji} {bot_status['status'].upper()}")
    if 'start_time' in bot_status and bot_status['start_time'] != 'Unknown':
        print(f"⏰ Запущен: {bot_status['start_time']}")
    print()
    
    # Ресурсы системы
    print("💻 ИСПОЛЬЗОВАНИЕ РЕСУРСОВ:")
    print(f"🔥 CPU: {system_info['cpu']['percent']:.1f}% ({system_info['cpu']['cores']} cores)")
    
    memory_bar = "█" * int(system_info['memory']['percent'] / 5) + "░" * (20 - int(system_info['memory']['percent'] / 5))
    print(f"🧠 RAM: {system_info['memory']['percent']:.1f}% [{memory_bar}]")
    print(f"     {system_info['memory']['used_gb']:.2f} GB / {system_info['memory']['total_gb']:.2f} GB")
    
    disk_bar = "█" * int(system_info['disk']['percent'] / 5) + "░" * (20 - int(system_info['disk']['percent'] / 5))
    print(f"💾 Диск: {system_info['disk']['percent']:.1f}% [{disk_bar}]")
    print(f"      {system_info['disk']['used_gb']:.2f} GB / {system_info['disk']['total_gb']:.2f} GB")
    
    print(f"🌐 Сеть: ↑{format_bytes(system_info['network']['bytes_sent'])} ↓{format_bytes(system_info['network']['bytes_recv'])}")
    print()
    
    # Предупреждения
    warnings = []
    if system_info['memory']['percent'] > 80:
        warnings.append("⚠️  Высокое использование памяти!")
    if system_info['disk']['percent'] > 90:
        warnings.append("⚠️  Мало места на диске!")
    if bot_status['status'] != 'running':
        warnings.append("🚨 Telegram бот не запущен!")
    
    if warnings:
        print("🚨 ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    
    # Oracle Cloud Always Free лимиты
    print("📏 ORACLE CLOUD ALWAYS FREE ЛИМИТЫ:")
    print(f"   RAM: {system_info['memory']['total_gb']:.1f} GB из 1.0 GB (лимит)")
    print(f"   CPU: 1/8 OCPU (Always Free)")
    print(f"   Диск: {system_info['disk']['total_gb']:.1f} GB из 200 GB (лимит)")
    print("=" * 60)

if __name__ == "__main__":
    print_status()
