#!/usr/bin/env python3
"""
Модуль для работы с базой данных статистики
Использует SQLite для хранения данных о пользователях и транзакциях
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = os.getenv('DATABASE_PATH', 'bot_stats.db')


class Database:
    """Класс для работы с базой данных статистики"""
    
    def __init__(self, db_path: str = DB_PATH):
        """
        Инициализация базы данных
        
        :param db_path: путь к файлу базы данных
        """
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с подключением"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Доступ к колонкам по имени
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Инициализация таблиц базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_requests INTEGER DEFAULT 0,
                    is_admin BOOLEAN DEFAULT 0
                )
            ''')
            
            # Таблица транзакций (QR-кодов)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    service TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица событий (действия пользователей)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Индексы для быстрого поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def add_or_update_user(self, user_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None,
                          is_admin: bool = False):
        """
        Добавить или обновить информацию о пользователе
        
        :param user_id: Telegram ID пользователя
        :param username: Username пользователя
        :param first_name: Имя пользователя
        :param last_name: Фамилия пользователя
        :param is_admin: Флаг администратора
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем существование пользователя
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Обновляем существующего
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, 
                        last_seen = CURRENT_TIMESTAMP, total_requests = total_requests + 1
                    WHERE user_id = ?
                ''', (username, first_name, last_name, user_id))
            else:
                # Добавляем нового
                cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, is_admin, total_requests)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (user_id, username, first_name, last_name, is_admin))
    
    def add_transaction(self, user_id: int, amount: float, service: str = None):
        """
        Добавить транзакцию (создание QR-кода)
        
        :param user_id: ID пользователя
        :param amount: Сумма транзакции
        :param service: Название услуги
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, service)
                VALUES (?, ?, ?)
            ''', (user_id, amount, service))
            logger.info(f"Transaction added: user={user_id}, amount={amount}, service={service}")
    
    def add_event(self, user_id: int, event_type: str, event_data: str = None):
        """
        Добавить событие
        
        :param user_id: ID пользователя
        :param event_type: Тип события (start, payment, help, info, etc.)
        :param event_data: Дополнительные данные
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (user_id, event_type, event_data)
                VALUES (?, ?, ?)
            ''', (user_id, event_type, event_data))
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """
        Получить статистику пользователя
        
        :param user_id: ID пользователя
        :return: Словарь со статистикой или None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Основная информация
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return None
            
            # Количество транзакций
            cursor.execute('SELECT COUNT(*) as count FROM transactions WHERE user_id = ?', (user_id,))
            transactions_count = cursor.fetchone()['count']
            
            # Общая сумма
            cursor.execute('SELECT SUM(amount) as total FROM transactions WHERE user_id = ?', (user_id,))
            total_amount = cursor.fetchone()['total'] or 0
            
            return {
                'user_id': user['user_id'],
                'username': user['username'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'first_seen': user['first_seen'],
                'last_seen': user['last_seen'],
                'total_requests': user['total_requests'],
                'transactions_count': transactions_count,
                'total_amount': total_amount
            }
    
    def get_all_users_stats(self) -> List[Dict]:
        """
        Получить статистику всех пользователей
        
        :return: Список словарей со статистикой
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.last_name,
                    u.total_requests,
                    COUNT(t.id) as transactions_count,
                    COALESCE(SUM(t.amount), 0) as total_amount,
                    u.last_seen
                FROM users u
                LEFT JOIN transactions t ON u.user_id = t.user_id
                GROUP BY u.user_id
                ORDER BY u.total_requests DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_stats(self) -> Dict:
        """
        Получить общую статистику бота
        
        :return: Словарь с общей статистикой
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Всего пользователей
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            # Всего транзакций
            cursor.execute('SELECT COUNT(*) as count FROM transactions')
            total_transactions = cursor.fetchone()['count']
            
            # Общая сумма
            cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM transactions')
            total_amount = cursor.fetchone()['total']
            
            # Средняя сумма
            cursor.execute('SELECT COALESCE(AVG(amount), 0) as avg FROM transactions')
            avg_amount = cursor.fetchone()['avg']
            
            # Активных за последние 24 часа
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as count 
                FROM events 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            active_24h = cursor.fetchone()['count']
            
            return {
                'total_users': total_users,
                'total_transactions': total_transactions,
                'total_amount': round(total_amount, 2),
                'avg_amount': round(avg_amount, 2),
                'active_24h': active_24h
            }
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """
        Получить последние транзакции
        
        :param limit: Количество транзакций
        :return: Список словарей с транзакциями
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    t.id,
                    t.user_id,
                    u.username,
                    u.first_name,
                    t.amount,
                    t.service,
                    t.timestamp
                FROM transactions t
                JOIN users u ON t.user_id = u.user_id
                ORDER BY t.timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_popular_services(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Получить популярные услуги
        
        :param limit: Количество услуг
        :return: Список кортежей (услуга, количество)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT service, COUNT(*) as count
                FROM transactions
                WHERE service IS NOT NULL AND service != ''
                GROUP BY service
                ORDER BY count DESC
                LIMIT ?
            ''', (limit,))
            
            return [(row['service'], row['count']) for row in cursor.fetchall()]
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """
        Получить статистику по дням
        
        :param days: Количество дней
        :return: Список словарей с дневной статистикой
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as transactions,
                    COALESCE(SUM(amount), 0) as total_amount
                FROM transactions
                WHERE timestamp > datetime('now', '-' || ? || ' days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''', (days,))
            
            return [dict(row) for row in cursor.fetchall()]


# Создаем глобальный экземпляр
db = Database()


if __name__ == '__main__':
    # Тестирование
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing database module...")
    
    # Тест добавления пользователя
    db.add_or_update_user(123456, 'testuser', 'Test', 'User')
    print("✅ User added")
    
    # Тест добавления транзакции
    db.add_transaction(123456, 1500.0, 'LAMINACE RAS')
    print("✅ Transaction added")
    
    # Тест получения статистики
    stats = db.get_user_stats(123456)
    print(f"✅ User stats: {stats}")
    
    # Общая статистика
    total = db.get_total_stats()
    print(f"✅ Total stats: {total}")
    
    print("✅ All tests passed!")
