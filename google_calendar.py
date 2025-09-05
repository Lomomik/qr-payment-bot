#!/usr/bin/env python3
"""
Модуль для работы с Google Calendar API
Получает сегодняшние встречи и определяет цены по названию процедур
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env.test')

logger = logging.getLogger(__name__)

# Права доступа для Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Словарь соответствия процедур и цен (CZK)
PROCEDURE_PRICES = {
    # Услуги для бровей
    'úprava obočí': 800,
    'úprava a barvení obočí': 1000,
    'úprava': 800,
    'barvení obočí': 600,
    'zesvětlení obočí': 1200,
    'zesvětlení s úpravou': 1400,
    'zesvětlení s úpravou a tonováním': 1600,
    'laminace obočí': 1400,
    'laminace s úpravou': 1600,
    'laminace s úpravou a tonováním': 1800,
    
    # Услуги для ресниц
    'laminace řas': 1500,
    'barvení řas': 500,
    'botox řas': 1600,
    
    # Комбинированные услуги
    'laminace řas + úprava obočí': 2000,
    'laminace řas + barvení obočí': 1800,
    'laminace řas + úprava a barvení obočí': 2200,
    'laminace řas + zesvětlení obočí': 2400,
    'laminace obočí a řas': 2500,
    
    # Депиляция и уход
    'depilace obličeje': 800,
    'depilace horní ret': 300,
    'depilace brady': 400,
    
    # Красота и стиль
    'líčení': 1200,
    'účes': 1000,
    'líčení & účes': 2000,
    'svatební líčení': 2500,
    'večerní líčení': 1800,
    
    # Консультации
    'konzultace': 500,
    'konzultace + návrh': 800,
}

# Альтернативные названия процедур (для поиска)
PROCEDURE_ALIASES = {
    'obočí': 'úprava obočí',
    'řasy': 'laminace řas',
    'barvení': 'barvení obočí',
    'zesvětlení': 'zesvětlení obočí',
    'laminace': 'laminace řas',
    'líčení svatební': 'svatební líčení',
    'večerní': 'večerní líčení',
    'depilace': 'depilace obličeje',
    'konzultace návrh': 'konzultace + návrh',
}

class GoogleCalendarService:
    """Сервис для работы с Google Calendar"""
    
    def __init__(self):
        self.service = None
        self.creds = None
        
        # Получаем настройки из переменных окружения
        self.auth_type = os.getenv('GOOGLE_CALENDAR_TYPE', 'oauth')  # oauth или service_account
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        if self.auth_type == 'service_account':
            self.service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account.json')
        else:
            self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
            self.token_file = 'token.json'
        
    def authenticate(self) -> bool:
        """Аутентификация в Google Calendar"""
        try:
            if self.auth_type == 'service_account':
                return self._authenticate_service_account()
            else:
                return self._authenticate_oauth()
                
        except FileNotFoundError as e:
            logger.error(f"❌ Файл не найден: {e}")
            logger.info("📋 Выполните настройку согласно REAL_GOOGLE_CALENDAR_SETUP.md")
            return False
        except Exception as e:
            logger.error(f"❌ Google Calendar authentication failed: {e}")
            logger.info("📋 Проверьте настройки в REAL_GOOGLE_CALENDAR_SETUP.md")
            return False
    
    def _authenticate_service_account(self) -> bool:
        """Аутентификация через Service Account (для сервера)"""
        if not os.path.exists(self.service_account_file):
            logger.error(f"Service Account файл не найден: {self.service_account_file}")
            logger.info("Создайте Service Account согласно REAL_GOOGLE_CALENDAR_SETUP.md")
            return False
        
        # Создаем credentials из Service Account
        self.creds = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=SCOPES)
        
        # Создаем сервис
        self.service = build('calendar', 'v3', credentials=self.creds)
        logger.info("✅ Google Calendar Service Account authentication successful")
        return True
    
    def _authenticate_oauth(self) -> bool:
        """Аутентификация через OAuth (для локального тестирования)"""
        # Проверяем существующий токен
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # Если токен недействителен, обновляем или создаем новый
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"OAuth credentials файл не найден: {self.credentials_file}")
                    logger.info("Создайте credentials.json согласно REAL_GOOGLE_CALENDAR_SETUP.md")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Сохраняем токен для следующего использования
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        
        # Создаем сервис
        self.service = build('calendar', 'v3', credentials=self.creds)
        logger.info("✅ Google Calendar OAuth authentication successful")
        return True
    
    def get_today_events(self) -> List[Dict]:
        """Получает события на сегодня"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Определяем временные рамки для сегодняшнего дня
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Запрос к API
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=today.isoformat() + 'Z',
                timeMax=tomorrow.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} events for today from calendar: {self.calendar_id}")
            
            return events
            
        except HttpError as error:
            logger.error(f"Error getting calendar events: {error}")
            if "notFound" in str(error):
                logger.error(f"Calendar ID '{self.calendar_id}' not found or no access")
                logger.info("Проверьте GOOGLE_CALENDAR_ID в .env.test")
                if self.auth_type == 'service_account':
                    logger.info("Убедитесь, что Service Account имеет доступ к календарю")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting calendar events: {e}")
            return []

def extract_procedure_from_title(title: str) -> Optional[str]:
    """Извлекает название процедуры из заголовка события"""
    if not title:
        return None
    
    title_lower = title.lower().strip()
    
    # Ищем точное совпадение в основном словаре
    for procedure in PROCEDURE_PRICES.keys():
        if procedure.lower() in title_lower:
            return procedure
    
    # Ищем через алиасы
    for alias, procedure in PROCEDURE_ALIASES.items():
        if alias.lower() in title_lower:
            return procedure
    
    return None

def get_procedure_price(procedure: str) -> Optional[int]:
    """Получает цену процедуры"""
    return PROCEDURE_PRICES.get(procedure.lower())

def format_event_info(event: Dict) -> Tuple[str, Optional[str], Optional[int]]:
    """Форматирует информацию о событии для отображения"""
    title = event.get('summary', 'Без названия')
    
    # Получаем время начала
    start = event.get('start', {})
    if 'dateTime' in start:
        start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
        time_str = start_time.strftime('%H:%M')
    elif 'date' in start:
        time_str = 'Весь день'
    else:
        time_str = 'Время не указано'
    
    # Определяем процедуру и цену
    procedure = extract_procedure_from_title(title)
    price = get_procedure_price(procedure) if procedure else None
    
    # Форматируем для отображения
    if procedure and price:
        display_text = f"🕐 {time_str} | {procedure.title()} - {price} CZK"
    else:
        display_text = f"🕐 {time_str} | {title} - Цена не определена"
    
    return display_text, procedure, price

def parse_events_for_payment(events: List[Dict]) -> List[Dict]:
    """Парсит события для создания кнопок оплаты"""
    payment_options = []
    
    for event in events:
        display_text, procedure, price = format_event_info(event)
        
        if procedure and price:
            payment_options.append({
                'display_text': display_text,
                'procedure': procedure,
                'price': price,
                'event_id': event.get('id', ''),
                'event_title': event.get('summary', '')
            })
    
    return payment_options

# Функция для тестирования (без реального API)
def get_mock_today_events() -> List[Dict]:
    """Возвращает тестовые события для разработки"""
    now = datetime.now()
    
    mock_events = [
        {
            'id': 'test1',
            'summary': 'Laminace řas + úprava obočí - Anna',
            'start': {'dateTime': (now.replace(hour=9, minute=0)).isoformat() + 'Z'},
            'end': {'dateTime': (now.replace(hour=10, minute=30)).isoformat() + 'Z'}
        },
        {
            'id': 'test2', 
            'summary': 'Zesvětlení s úpravou a tonováním - Marie',
            'start': {'dateTime': (now.replace(hour=11, minute=0)).isoformat() + 'Z'},
            'end': {'dateTime': (now.replace(hour=12, minute=30)).isoformat() + 'Z'}
        },
        {
            'id': 'test3',
            'summary': 'Líčení & účes - Petra',
            'start': {'dateTime': (now.replace(hour=14, minute=0)).isoformat() + 'Z'},
            'end': {'dateTime': (now.replace(hour=16, minute=0)).isoformat() + 'Z'}
        },
        {
            'id': 'test4',
            'summary': 'Konzultace + návrh - Elena',
            'start': {'dateTime': (now.replace(hour=16, minute=30)).isoformat() + 'Z'},
            'end': {'dateTime': (now.replace(hour=17, minute=30)).isoformat() + 'Z'}
        }
    ]
    
    return mock_events

# Инициализация сервиса (будет использоваться в боте)
calendar_service = GoogleCalendarService()

if __name__ == '__main__':
    # Тестирование функций
    print("🧪 Тестирование Google Calendar модуля")
    
    # Тест парсинга мок-событий
    mock_events = get_mock_today_events()
    print(f"\n📅 Найдено {len(mock_events)} тестовых событий:")
    
    payment_options = parse_events_for_payment(mock_events)
    for option in payment_options:
        print(f"  {option['display_text']}")
    
    # Тест определения процедур
    test_titles = [
        "Laminace řas - Anna",
        "Úprava a barvení obočí - Marie", 
        "Konzultace něco",
        "Встреча с клиентом"
    ]
    
    print(f"\n🔍 Тест определения процедур:")
    for title in test_titles:
        procedure = extract_procedure_from_title(title)
        price = get_procedure_price(procedure) if procedure else None
        print(f"  '{title}' → {procedure} → {price} CZK")
