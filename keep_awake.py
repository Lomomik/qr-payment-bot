"""
Внешний пинг сервис для поддержания Render приложения в активном состоянии
Запустите этот скрипт на любом другом сервере (Oracle Cloud, дома, VPS)
"""

import requests
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL вашего Render приложения (замените на ваш)
RENDER_APP_URL = "https://your-qr-bot.onrender.com"
PING_INTERVAL = 600  # 10 минут в секундах

def ping_app():
    """Пингует Render приложение"""
    try:
        response = requests.get(f"{RENDER_APP_URL}/health", timeout=30)
        if response.status_code == 200:
            logger.info(f"✅ Ping successful at {datetime.now()}")
            return True
        else:
            logger.warning(f"⚠️ Ping returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ping failed: {e}")
        return False

def main():
    """Главная функция пинг сервиса"""
    logger.info(f"🚀 Starting ping service for {RENDER_APP_URL}")
    logger.info(f"⏰ Ping interval: {PING_INTERVAL // 60} minutes")
    
    while True:
        ping_app()
        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    main()
