#!/usr/bin/env python3
"""
Универсальный модуль для работы с базой данных
Поддерживает PostgreSQL (для Render) и SQLite (для локальной разработки)
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from contextlib import contextmanager
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Определяем тип БД из переменной окружения
DATABASE_URL = os.getenv('DATABASE_URL')

# Определяем какую БД использовать
if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    DB_TYPE = 'postgresql'
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import psycopg2.pool
        POSTGRESQL_AVAILABLE = True
        logger.info("🐘 PostgreSQL driver loaded successfully")
    except ImportError:
        POSTGRESQL_AVAILABLE = False
        logger.error("❌ psycopg2 not found! Install: pip install psycopg2-binary")
        logger.info("🔄 Falling back to SQLite")
        DB_TYPE = 'sqlite'  # Fallback
else:
    DB_TYPE = 'sqlite'
    POSTGRESQL_AVAILABLE = False

logger.info(f"📊 Database type: {DB_TYPE}")


class Database:
    """Универсальный класс для работы с базой данных"""
    
    def __init__(self):
        """Инициализация базы данных"""
        self.db_type = DB_TYPE
        
        if self.db_type == 'postgresql' and POSTGRESQL_AVAILABLE:
            self._init_postgresql()
        else:
            self._init_sqlite()
        
        self.init_db()
    
    def _init_postgresql(self):
        """Инициализация PostgreSQL"""
        # Парсим DATABASE_URL
        url = urlparse(DATABASE_URL)
        
        self.pg_config = {
            'host': url.hostname,
            'port': url.port or 5432,
            'database': url.path[1:],  # Убираем первый /
            'user': url.username,
            'password': url.password,
            'sslmode': 'require'  # Render требует SSL
        }
        
        # Создаем connection pool для эффективности
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **self.pg_config
            )
            logger.info(f"✅ Connected to PostgreSQL: {self.pg_config['database']}")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection error: {e}")
            raise
    
    def _init_sqlite(self):
        """Инициализация SQLite"""
        self.db_path = os.getenv('DATABASE_PATH', 'bot_stats.db')
        logger.info(f"📝 Using SQLite: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с подключением"""
        if self.db_type == 'postgresql':
            conn = self.pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                self.pool.putconn(conn)
        else:
            # SQLite
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                conn.close()
    
    def _get_cursor(self, conn):
        """Получить cursor с правильным типом для текущей БД"""
        if self.db_type == 'postgresql':
            return conn.cursor(cursor_factory=RealDictCursor)
        else:
            return conn.cursor()
    
    def init_db(self):
        """Инициализация таблиц базы данных"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                # PostgreSQL синтаксис
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_requests INTEGER DEFAULT 0,
                        is_admin BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        service TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                ''')
                
                # Индексы
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
                
            else:
                # SQLite синтаксис
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
                
                # Индексы
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
            
            conn.commit()
            logger.info(f"Database initialized successfully")
    
    def add_or_update_user(self, user_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None,
                          is_admin: bool = False):
        """Добавить или обновить информацию о пользователе"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
            # Проверяем существование пользователя
            cursor.execute('SELECT user_id FROM users WHERE user_id = %s' if self.db_type == 'postgresql' else 'SELECT user_id FROM users WHERE user_id = ?', 
                         (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Обновляем существующего
                cursor.execute('''
                    UPDATE users 
                    SET username = %s, first_name = %s, last_name = %s, 
                        last_seen = CURRENT_TIMESTAMP, total_requests = total_requests + 1
                    WHERE user_id = %s
                ''' if self.db_type == 'postgresql' else '''
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, 
                        last_seen = CURRENT_TIMESTAMP, total_requests = total_requests + 1
                    WHERE user_id = ?
                ''', (username, first_name, last_name, user_id))
            else:
                # Добавляем нового
                cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, is_admin, total_requests)
                    VALUES (%s, %s, %s, %s, %s, 1)
                ''' if self.db_type == 'postgresql' else '''
                    INSERT INTO users (user_id, username, first_name, last_name, is_admin, total_requests)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (user_id, username, first_name, last_name, is_admin))
    
    def add_transaction(self, user_id: int, amount: float, service: str = None):
        """Добавить транзакцию"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, service)
                VALUES (%s, %s, %s)
            ''' if self.db_type == 'postgresql' else '''
                INSERT INTO transactions (user_id, amount, service)
                VALUES (?, ?, ?)
            ''', (user_id, amount, service))
            logger.info(f"Transaction added: user={user_id}, amount={amount}, service={service}")
    
    def add_event(self, user_id: int, event_type: str, event_data: str = None):
        """Добавить событие"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            cursor.execute('''
                INSERT INTO events (user_id, event_type, event_data)
                VALUES (%s, %s, %s)
            ''' if self.db_type == 'postgresql' else '''
                INSERT INTO events (user_id, event_type, event_data)
                VALUES (?, ?, ?)
            ''', (user_id, event_type, event_data))
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Получить статистику пользователя"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
            cursor.execute('SELECT * FROM users WHERE user_id = %s' if self.db_type == 'postgresql' else 'SELECT * FROM users WHERE user_id = ?', 
                         (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return None
            
            cursor.execute('SELECT COUNT(*) as count FROM transactions WHERE user_id = %s' if self.db_type == 'postgresql' else 'SELECT COUNT(*) as count FROM transactions WHERE user_id = ?', 
                         (user_id,))
            transactions_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT SUM(amount) as total FROM transactions WHERE user_id = %s' if self.db_type == 'postgresql' else 'SELECT SUM(amount) as total FROM transactions WHERE user_id = ?', 
                         (user_id,))
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
                'total_amount': float(total_amount)
            }
    
    def get_all_users_stats(self) -> List[Dict]:
        """Получить статистику всех пользователей"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
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
                GROUP BY u.user_id, u.username, u.first_name, u.last_name, u.total_requests, u.last_seen
                ORDER BY u.total_requests DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_stats(self) -> Dict:
        """Получить общую статистику бота"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM transactions')
            total_transactions = cursor.fetchone()['count']
            
            cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM transactions')
            total_amount = cursor.fetchone()['total']
            
            cursor.execute('SELECT COALESCE(AVG(amount), 0) as avg FROM transactions')
            avg_amount = cursor.fetchone()['avg']
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as count 
                FROM events 
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 day'
            ''' if self.db_type == 'postgresql' else '''
                SELECT COUNT(DISTINCT user_id) as count 
                FROM events 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            active_24h = cursor.fetchone()['count']
            
            return {
                'total_users': total_users,
                'total_transactions': total_transactions,
                'total_amount': round(float(total_amount), 2),
                'avg_amount': round(float(avg_amount), 2),
                'active_24h': active_24h
            }
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """Получить последние транзакции"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
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
                LIMIT %s
            ''' if self.db_type == 'postgresql' else '''
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
        """Получить популярные услуги"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
            cursor.execute('''
                SELECT service, COUNT(*) as count
                FROM transactions
                WHERE service IS NOT NULL AND service != ''
                GROUP BY service
                ORDER BY count DESC
                LIMIT %s
            ''' if self.db_type == 'postgresql' else '''
                SELECT service, COUNT(*) as count
                FROM transactions
                WHERE service IS NOT NULL AND service != ''
                GROUP BY service
                ORDER BY count DESC
                LIMIT ?
            ''', (limit,))
            
            return [(row['service'], row['count']) for row in cursor.fetchall()]
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Получить статистику по дням"""
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
            cursor.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as transactions,
                    COALESCE(SUM(amount), 0) as total_amount
                FROM transactions
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '%s days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''' if self.db_type == 'postgresql' else '''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as transactions,
                    COALESCE(SUM(amount), 0) as total_amount
                FROM transactions
                WHERE timestamp > datetime('now', '-' || ? || ' days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''', (days,) if self.db_type == 'postgresql' else (days,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_monthly_stats(self, month_offset: int = 0) -> Dict:
        """Получить статистику за месяц
        
        Args:
            month_offset: 0 = текущий месяц, 1 = прошлый месяц, и т.д.
        
        Returns:
            Dict с ключами: month, year, transactions, total_amount, avg_amount, unique_users
        """
        with self.get_connection() as conn:
            cursor = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT 
                        EXTRACT(MONTH FROM timestamp) as month,
                        EXTRACT(YEAR FROM timestamp) as year,
                        COUNT(*) as transactions,
                        COALESCE(SUM(amount), 0) as total_amount,
                        COALESCE(AVG(amount), 0) as avg_amount,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM transactions
                    WHERE 
                        EXTRACT(YEAR FROM timestamp) = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '%s months')
                        AND EXTRACT(MONTH FROM timestamp) = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '%s months')
                    GROUP BY EXTRACT(MONTH FROM timestamp), EXTRACT(YEAR FROM timestamp)
                ''', (month_offset, month_offset))
            else:
                cursor.execute('''
                    SELECT 
                        CAST(strftime('%m', timestamp) AS INTEGER) as month,
                        CAST(strftime('%Y', timestamp) AS INTEGER) as year,
                        COUNT(*) as transactions,
                        COALESCE(SUM(amount), 0) as total_amount,
                        COALESCE(AVG(amount), 0) as avg_amount,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM transactions
                    WHERE 
                        strftime('%Y-%m', timestamp) = strftime('%Y-%m', date('now', '-' || ? || ' months'))
                    GROUP BY strftime('%Y-%m', timestamp)
                ''', (month_offset,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'month': int(result['month']),
                    'year': int(result['year']),
                    'transactions': result['transactions'],
                    'total_amount': round(float(result['total_amount']), 2),
                    'avg_amount': round(float(result['avg_amount']), 2),
                    'unique_users': result['unique_users']
                }
            else:
                # Возвращаем пустую статистику если нет данных
                from datetime import datetime, timedelta
                target_date = datetime.now() - timedelta(days=30 * month_offset)
                return {
                    'month': target_date.month,
                    'year': target_date.year,
                    'transactions': 0,
                    'total_amount': 0.0,
                    'avg_amount': 0.0,
                    'unique_users': 0
                }
    
    def close(self):
        """Закрыть подключение"""
        if self.db_type == 'postgresql' and hasattr(self, 'pool'):
            self.pool.closeall()
            logger.info("PostgreSQL connection pool closed")


# Создаем глобальный экземпляр
db = Database()


if __name__ == '__main__':
    # Тестирование
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing database module...")
    print(f"Database type: {db.db_type}")
    
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
