#!/usr/bin/env python3
"""
Keep-Alive модуль для предотвращения засыпания на Render
Добавьте этот код в ваш основной файл бота
"""

import asyncio
import aiohttp
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class RenderKeepAlive:
    """Класс для поддержания активности Render сервиса"""
    
    def __init__(self, app_url: str = None, ping_interval: int = 300):
        """
        :param app_url: URL вашего Render приложения
        :param ping_interval: Интервал пинга в секундах (по умолчанию 5 минут)
        """
        self.app_url = app_url or os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:8080')
        self.ping_interval = ping_interval
        self.is_running = False
        
    async def ping_self(self):
        """Пингует собственный health endpoint"""
        try:
            # Используем ClientTimeout согласно Context7 рекомендациям
            timeout = aiohttp.ClientTimeout(
                total=10,           # Общий таймаут
                sock_connect=5,     # Таймаут подключения к сокету
                sock_read=5         # Таймаут чтения сокета
            )
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.app_url}/health") as response:
                    if response.status == 200:
                        logger.info(f"✅ Keep-alive ping successful: {datetime.now().strftime('%H:%M:%S')}")
                        return True
                    else:
                        logger.warning(f"⚠️ Keep-alive ping failed with status: {response.status}")
                        return False
        except asyncio.TimeoutError:
            logger.warning("⏰ Keep-alive ping timeout")
            return False
        except aiohttp.ClientConnectorError as e:
            logger.warning(f"🔌 Keep-alive connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Keep-alive ping error: {e}")
            return False
    
    async def keep_alive_loop(self):
        """Основной цикл keep-alive"""
        logger.info(f"🚀 Starting keep-alive service for {self.app_url}")
        logger.info(f"⏰ Ping interval: {self.ping_interval // 60} minutes")
        
        self.is_running = True
        
        # Ждем 30 секунд перед первым пингом (дает время боту запуститься)
        await asyncio.sleep(30)
        
        while self.is_running:
            await self.ping_self()
            await asyncio.sleep(self.ping_interval)
    
    def start(self):
        """Запускает keep-alive как фоновую задачу"""
        if not self.is_running:
            asyncio.create_task(self.keep_alive_loop())
            logger.info("🔄 Keep-alive task started")
    
    def stop(self):
        """Останавливает keep-alive"""
        self.is_running = False
        logger.info("⏹️ Keep-alive task stopped")

# Создание глобального экземпляра
render_keep_alive = RenderKeepAlive()

# Health endpoint для Flask (если используете Flask)
def create_flask_health_endpoint():
    """Создает Flask приложение с health endpoint"""
    try:
        from flask import Flask
        import threading
        
        app = Flask(__name__)
        
        @app.route('/health')
        def health():
            return {
                "status": "ok", 
                "service": "qr-payment-bot",
                "timestamp": datetime.now().isoformat()
            }, 200
        
        @app.route('/')
        def home():
            return {
                "message": "QR Payment Bot is running",
                "status": "active",
                "timestamp": datetime.now().isoformat()
            }, 200
        
        def run_flask():
            app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False)
        
        # Запуск Flask в отдельном потоке
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        logger.info("🌐 Flask health endpoint started on port 8080")
        
    except ImportError:
        logger.warning("Flask not available, skipping health endpoint")

# Простой HTTP сервер (если нет Flask/FastAPI)
def create_simple_health_endpoint():
    """Создает простой HTTP сервер с health endpoint"""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        import threading
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    response = {
                        "status": "ok",
                        "service": "qr-payment-bot",
                        "timestamp": datetime.now().isoformat()
                    }
                elif self.path == '/':
                    response = {
                        "message": "QR Payment Bot is running",
                        "status": "active", 
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            
            def log_message(self, format, *args):
                # Подавляем логи HTTP сервера
                pass
        
        def run_simple_server():
            server = HTTPServer(('0.0.0.0', int(os.getenv('PORT', 8080))), HealthHandler)
            server.serve_forever()
        
        # Запуск в отдельном потоке
        server_thread = threading.Thread(target=run_simple_server, daemon=True)
        server_thread.start()
        
        logger.info("🌐 Simple HTTP health endpoint started on port 8080")
        
    except Exception as e:
        logger.error(f"❌ Failed to start simple health endpoint: {e}")

def setup_render_keep_alive(app_url: str = None):
    """
    Настройка keep-alive для Render
    
    :param app_url: URL вашего Render приложения (например: https://your-app.onrender.com)
    :return: корутину для запуска в asyncio.create_task()
    """
    
    # Определяем URL автоматически для Render
    if not app_url:
        app_url = os.getenv('RENDER_EXTERNAL_URL')
        if not app_url and os.getenv('RENDER'):
            # Пытаемся определить URL по имени сервиса
            service_name = os.getenv('RENDER_SERVICE_NAME', 'qr-payment-bot')
            app_url = f"https://{service_name}.onrender.com"
    
    if app_url:
        render_keep_alive.app_url = app_url
        logger.info(f"🔧 Keep-alive configured for: {app_url}")
    
    # Создаем health endpoint
    if os.getenv('FLASK_APP'):
        create_flask_health_endpoint()
    else:
        create_simple_health_endpoint()
    
    # Возвращаем корутину для запуска
    return render_keep_alive.keep_alive_loop()

if __name__ == "__main__":
    # Тестовый запуск
    import logging
    logging.basicConfig(level=logging.INFO)
    
    setup_render_keep_alive("https://your-app.onrender.com")
    
    # Эмуляция работы бота
    try:
        asyncio.run(asyncio.sleep(3600))  # Работаем час
    except KeyboardInterrupt:
        print("Stopping...")
        render_keep_alive.stop()
