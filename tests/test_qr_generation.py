"""
Тесты для генерации QR-кодов
"""
import sys
import os
from io import BytesIO

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from qr import generate_qr_code


class TestQRCodeGeneration:
    """Тесты генерации QR-кодов"""
    
    def test_generate_qr_basic(self):
        """Тест базовой генерации QR-кода без услуги"""
        result = generate_qr_code(1000.0)
        
        assert isinstance(result, BytesIO)
        assert result.getvalue() is not None
        assert len(result.getvalue()) > 0
    
    def test_generate_qr_with_service(self):
        """Тест генерации QR-кода с указанием услуги"""
        result = generate_qr_code(1500.0, "LAMINACE RAS")
        
        assert isinstance(result, BytesIO)
        assert result.getvalue() is not None
        assert len(result.getvalue()) > 0
    
    def test_generate_qr_integer_amount(self):
        """Тест с целой суммой"""
        result = generate_qr_code(800)
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0
    
    def test_generate_qr_decimal_amount(self):
        """Тест с десятичной суммой"""
        result = generate_qr_code(1234.56)
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0
    
    def test_generate_qr_small_amount(self):
        """Тест с малой суммой"""
        result = generate_qr_code(100.0)
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0
    
    def test_generate_qr_large_amount(self):
        """Тест с большой суммой"""
        result = generate_qr_code(50000.0)
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0
    
    def test_generate_qr_with_long_service_name(self):
        """Тест с длинным названием услуги"""
        long_service = "LAMINACE RAS + UPRAVA A BARVENI OBOCI"
        result = generate_qr_code(2200.0, long_service)
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0
    
    def test_generate_qr_with_special_characters(self):
        """Тест с специальными символами в названии услуги"""
        service = "ÚPRAVA & BARVENÍ OBOČÍ"
        result = generate_qr_code(1000.0, service)
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0


class TestServiceFiltering:
    """Тесты фильтрации услуг по сумме"""
    
    def test_services_for_low_amount(self):
        """Тест получения услуг для малой суммы (≤1000 CZK)"""
        from qr import get_services_for_amount, SERVICES_LOW_PRICE
        
        services = get_services_for_amount(800.0)
        assert services == SERVICES_LOW_PRICE
        
        services = get_services_for_amount(1000.0)
        assert services == SERVICES_LOW_PRICE
    
    def test_services_for_high_amount(self):
        """Тест получения услуг для большой суммы (>1000 CZK)"""
        from qr import get_services_for_amount, SERVICES_HIGH_PRICE
        
        services = get_services_for_amount(1001.0)
        assert services == SERVICES_HIGH_PRICE
        
        services = get_services_for_amount(2500.0)
        assert services == SERVICES_HIGH_PRICE
    
    def test_services_boundary(self):
        """Тест граничных значений фильтрации"""
        from qr import get_services_for_amount, SERVICES_LOW_PRICE, SERVICES_HIGH_PRICE
        
        # Ровно 1000 - должны быть low price услуги
        services_1000 = get_services_for_amount(1000.0)
        assert services_1000 == SERVICES_LOW_PRICE
        
        # 1000.01 - должны быть high price услуги
        services_1001 = get_services_for_amount(1000.01)
        assert services_1001 == SERVICES_HIGH_PRICE


class TestQRCodeFormat:
    """Тесты формата QR-кода"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Фикстура для мокирования переменных окружения"""
        monkeypatch.setenv('OWNER_NAME', 'TEST OWNER')
        monkeypatch.setenv('IBAN', 'CZ1234567890123456789')
    
    def test_qr_code_contains_correct_format(self, mock_env):
        """Тест правильности формата SPD"""
        # Это интеграционный тест - проверяем что QR генерируется
        # Полная проверка содержимого требует декодирования QR
        result = generate_qr_code(1500.0, "TEST SERVICE")
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 100  # QR код должен быть достаточно большим


# Параметризованные тесты
class TestParametrizedQRGeneration:
    """Параметризованные тесты для различных сценариев"""
    
    @pytest.mark.parametrize("amount,service", [
        (500, None),
        (800, "UPRAVA"),
        (1000, "BARVENI"),
        (1500, "LAMINACE RAS"),
        (2000, "LAMINACE RAS + UPRAVA"),
        (2500, "LICENI & UCES"),
    ])
    def test_various_amounts_and_services(self, amount, service):
        """Тест различных комбинаций сумм и услуг"""
        result = generate_qr_code(float(amount), service)
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0
    
    @pytest.mark.parametrize("amount", [
        100, 250.50, 500, 750.25, 1000, 1234.56, 2000, 5000
    ])
    def test_various_amounts_only(self, amount):
        """Тест различных сумм без услуг"""
        result = generate_qr_code(float(amount))
        
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
