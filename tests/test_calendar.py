"""
Тесты для модуля Google Calendar
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from google_calendar import (
    extract_procedure_from_title,
    get_procedure_price,
    format_event_info,
    parse_events_for_payment,
    get_mock_today_events,
    PROCEDURE_PRICES,
    PROCEDURE_ALIASES
)


class TestProcedureExtraction:
    """Тесты извлечения названия процедуры из заголовка"""
    
    def test_exact_match(self):
        """Тест точного совпадения"""
        title = "Laminace řas - Anna"
        procedure = extract_procedure_from_title(title)
        assert procedure == "laminace řas"
    
    def test_case_insensitive(self):
        """Тест регистронезависимости"""
        title = "ÚPRAVA OBOČÍ - Marie"
        procedure = extract_procedure_from_title(title)
        assert procedure == "úprava obočí"
    
    def test_with_client_name(self):
        """Тест с именем клиента"""
        title = "Zesvětlení obočí - Petra Nováková"
        procedure = extract_procedure_from_title(title)
        assert procedure == "zesvětlení obočí"
    
    def test_alias_match(self):
        """Тест распознавания через алиас"""
        title = "Obočí - Anna"
        procedure = extract_procedure_from_title(title)
        assert procedure in PROCEDURE_PRICES
    
    def test_no_match(self):
        """Тест когда процедура не найдена"""
        title = "Встреча с клиентом"
        procedure = extract_procedure_from_title(title)
        assert procedure is None
    
    def test_empty_title(self):
        """Тест с пустым названием"""
        procedure = extract_procedure_from_title("")
        assert procedure is None
    
    def test_none_title(self):
        """Тест с None в качестве названия"""
        procedure = extract_procedure_from_title(None)
        assert procedure is None


class TestProcedurePricing:
    """Тесты получения цены процедуры"""
    
    def test_get_price_valid_procedure(self):
        """Тест получения цены для существующей процедуры"""
        price = get_procedure_price("laminace řas")
        assert price == 1500
    
    def test_get_price_case_insensitive(self):
        """Тест регистронезависимости получения цены"""
        price = get_procedure_price("LAMINACE ŘAS")
        assert price == 1500
    
    def test_get_price_invalid_procedure(self):
        """Тест получения цены для несуществующей процедуры"""
        price = get_procedure_price("nonexistent procedure")
        assert price is None
    
    @pytest.mark.parametrize("procedure,expected_price", [
        ("úprava obočí", 800),
        ("úprava a barvení obočí", 1000),
        ("laminace řas", 1500),
        ("laminace řas + úprava obočí", 2000),
        ("svatební líčení", 2500),
    ])
    def test_various_procedures(self, procedure, expected_price):
        """Тест цен различных процедур"""
        price = get_procedure_price(procedure)
        assert price == expected_price


class TestEventFormatting:
    """Тесты форматирования информации о событиях"""
    
    def test_format_event_with_time(self):
        """Тест форматирования события со временем"""
        event = {
            'summary': 'Laminace řas - Anna',
            'start': {
                'dateTime': datetime.now().replace(hour=10, minute=30).isoformat() + 'Z'
            },
            'id': 'test123'
        }
        
        display_text, procedure, price = format_event_info(event)
        
        assert '10:30' in display_text
        assert procedure == 'laminace řas'
        assert price == 1500
    
    def test_format_event_all_day(self):
        """Тест форматирования события на весь день"""
        event = {
            'summary': 'Úprava obočí',
            'start': {
                'date': '2024-01-01'
            },
            'id': 'test456'
        }
        
        display_text, procedure, price = format_event_info(event)
        
        assert 'Весь день' in display_text or 'день' in display_text.lower()
    
    def test_format_event_no_procedure(self):
        """Тест форматирования события без процедуры"""
        event = {
            'summary': 'Встреча с клиентом',
            'start': {
                'dateTime': datetime.now().replace(hour=14, minute=0).isoformat() + 'Z'
            },
            'id': 'test789'
        }
        
        display_text, procedure, price = format_event_info(event)
        
        assert 'Встреча с клиентом' in display_text
        assert procedure is None
        assert price is None


class TestEventParsing:
    """Тесты парсинга событий для оплаты"""
    
    def test_parse_mock_events(self):
        """Тест парсинга тестовых событий"""
        events = get_mock_today_events()
        payment_options = parse_events_for_payment(events)
        
        assert len(payment_options) > 0
        assert all('display_text' in opt for opt in payment_options)
        assert all('procedure' in opt for opt in payment_options)
        assert all('price' in opt for opt in payment_options)
    
    def test_parse_empty_events(self):
        """Тест парсинга пустого списка событий"""
        payment_options = parse_events_for_payment([])
        assert payment_options == []
    
    def test_parsed_events_have_prices(self):
        """Тест что все распарсенные события имеют цены"""
        events = get_mock_today_events()
        payment_options = parse_events_for_payment(events)
        
        for option in payment_options:
            assert option['price'] is not None
            assert option['price'] > 0
    
    def test_parsed_events_structure(self):
        """Тест структуры распарсенных событий"""
        events = get_mock_today_events()
        payment_options = parse_events_for_payment(events)
        
        required_keys = ['display_text', 'procedure', 'price', 'event_id', 'event_title']
        
        for option in payment_options:
            for key in required_keys:
                assert key in option


class TestMockData:
    """Тесты для тестовых данных"""
    
    def test_mock_events_exist(self):
        """Тест что mock события создаются"""
        events = get_mock_today_events()
        assert len(events) > 0
    
    def test_mock_events_structure(self):
        """Тест структуры mock событий"""
        events = get_mock_today_events()
        
        for event in events:
            assert 'id' in event
            assert 'summary' in event
            assert 'start' in event
            assert 'end' in event
    
    def test_mock_events_today(self):
        """Тест что mock события на сегодня"""
        events = get_mock_today_events()
        today = datetime.now().date()
        
        for event in events:
            event_date = datetime.fromisoformat(
                event['start']['dateTime'].replace('Z', '+00:00')
            ).date()
            assert event_date == today


class TestPriceDictionary:
    """Тесты словаря цен"""
    
    def test_all_prices_positive(self):
        """Тест что все цены положительные"""
        for procedure, price in PROCEDURE_PRICES.items():
            assert price > 0
    
    def test_prices_reasonable(self):
        """Тест что цены в разумных пределах"""
        for procedure, price in PROCEDURE_PRICES.items():
            assert 100 <= price <= 10000  # CZK
    
    def test_aliases_point_to_existing_procedures(self):
        """Тест что алиасы указывают на существующие процедуры"""
        for alias, procedure in PROCEDURE_ALIASES.items():
            assert procedure in PROCEDURE_PRICES


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
