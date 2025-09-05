#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Google Calendar API
"""

import os
import logging
from dotenv import load_dotenv
from google_calendar import calendar_service, parse_events_for_payment, get_mock_today_events

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_google_calendar():
    """Тестирует подключение к Google Calendar"""
    print("🧪 Тестирование Google Calendar API")
    print("=" * 50)
    
    # Проверяем переменные окружения
    from dotenv import load_dotenv
    load_dotenv('.env.test')
    
    auth_type = os.getenv('GOOGLE_CALENDAR_TYPE', 'oauth')
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    
    print(f"🔧 Режим аутентификации: {auth_type}")
    print(f"📅 Calendar ID: {calendar_id}")
    
    # Проверяем файлы конфигурации в зависимости от типа
    if auth_type == 'service_account':
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account.json')
        credentials_exist = os.path.exists(service_account_file)
        print(f"🔑 Service Account файл: {'✅ найден' if credentials_exist else '❌ не найден'}")
        
        if not credentials_exist:
            print(f"\n❌ ОШИБКА: Файл {service_account_file} не найден!")
            print("📋 Следуйте инструкциям для Service Account в REAL_GOOGLE_CALENDAR_SETUP.md")
            print("🌐 Service Account подходит для серверного развертывания")
            return False
    else:
        credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        token_file = 'token.json'
        credentials_exist = os.path.exists(credentials_file)
        token_exist = os.path.exists(token_file)
        
        print(f"📄 OAuth credentials: {'✅ найден' if credentials_exist else '❌ не найден'}")
        print(f"🔑 OAuth token: {'✅ найден' if token_exist else '❌ будет создан при первом запуске'}")
        
        if not credentials_exist:
            print(f"\n❌ ОШИБКА: Файл {credentials_file} не найден!")
            print("📋 Следуйте инструкциям для OAuth в REAL_GOOGLE_CALENDAR_SETUP.md")
            print("🖥️ OAuth подходит только для локального тестирования")
            return False
    
    print(f"\n🔐 Попытка аутентификации ({auth_type})...")
    
    try:
        # Пробуем аутентификацию
        if calendar_service.authenticate():
            print("✅ Аутентификация успешна!")
            
            # Получаем события
            print("\n📅 Получение событий на сегодня...")
            events = calendar_service.get_today_events()
            
            print(f"📊 Найдено событий: {len(events)}")
            
            if events:
                print("\n📋 События:")
                payment_options = parse_events_for_payment(events)
                
                for i, option in enumerate(payment_options, 1):
                    print(f"  {i}. {option['display_text']}")
                    print(f"     Процедура: {option['procedure']}")
                    print(f"     Цена: {option['price']} CZK")
                    print()
                    
                if len(payment_options) == 0:
                    print("⚠️ События найдены, но процедуры не распознаны")
                    print("📋 Убедитесь, что названия событий содержат названия процедур")
                    print("   Например: 'Úprava obočí - Клиент'")
            else:
                print("ℹ️ На сегодня событий не найдено")
                print("💡 Создайте тестовые события в Google Calendar:")
                print("   - Úprava obočí - Клиент")
                print("   - Laminace řas - Клиент")
                print("   - Líčení - Клиент")
                
                if auth_type == 'service_account':
                    print("\n🔑 Для Service Account проверьте:")
                    print("   - Service Account email добавлен в настройки календаря")
                    print("   - Правильный Calendar ID в .env.test")
            
            return True
            
        else:
            print("❌ Ошибка аутентификации")
            print("📋 Проверьте настройки согласно REAL_GOOGLE_CALENDAR_SETUP.md")
            
            if auth_type == 'service_account':
                print("🔑 Для Service Account:")
                print("   - Проверьте правильность service-account.json")
                print("   - Убедитесь, что Service Account имеет доступ к календарю")
            
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("📋 Проверьте настройки согласно REAL_GOOGLE_CALENDAR_SETUP.md")
        return False

def test_mock_events():
    """Тестирует работу с мок-событиями"""
    print("\n🧪 Тестирование мок-событий")
    print("=" * 30)
    
    mock_events = get_mock_today_events()
    payment_options = parse_events_for_payment(mock_events)
    
    print(f"📊 Мок-событий: {len(mock_events)}")
    print(f"💰 Опций для оплаты: {len(payment_options)}")
    
    for i, option in enumerate(payment_options, 1):
        print(f"  {i}. {option['display_text']}")

if __name__ == '__main__':
    print("🚀 Запуск тестирования Google Calendar")
    print()
    
    # Тест реального API
    api_success = test_google_calendar()
    
    # Тест мок-данных
    test_mock_events()
    
    print("\n" + "=" * 50)
    if api_success:
        print("✅ Google Calendar API готов к использованию!")
        print("🚀 Можете запускать: python qr_test.py")
    else:
        print("⚠️ Google Calendar API недоступен")
        print("🔄 Бот будет работать с тестовыми данными")
        print("📋 Для реального API: REAL_GOOGLE_CALENDAR_SETUP.md")
