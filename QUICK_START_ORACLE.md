# Быстрый старт: Oracle Cloud Always Free

## 🎯 Краткая инструкция для опытных пользователей

### 1. Создайте аккаунт Oracle Cloud
- Перейдите на https://oracle.com/cloud/free/
- Зарегистрируйтесь (потребуется карта для верификации)

### 2. Создайте VM инстанс
- **Compute** → **Instances** → **Create Instance**
- **Shape**: `VM.Standard.E2.1.Micro` (Always Free)
- **Image**: Oracle Linux 8
- **SSH Keys**: Generate new pair, сохраните приватный ключ!

### 3. Настройте Security List
- **Networking** → **VCN** → **Security Lists** → **Default**
- **Add Ingress Rule**: Source `0.0.0.0/0`, TCP, Ports `80,443,8080`

### 4. Подключитесь по SSH
```bash
ssh -i your_private_key opc@YOUR_PUBLIC_IP
```

### 5. Настройте сервер одной командой
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/setup_oracle_server.sh | bash
```

Или вручную:
```bash
# Загрузите файл setup_oracle_server.sh и выполните:
chmod +x setup_oracle_server.sh
./setup_oracle_server.sh
```

### 6. Загрузите файлы бота
```bash
cd ~/telegram-bot

# Вариант 1: Через git (рекомендуется)
git clone https://github.com/YOUR_USERNAME/qr-payment-bot.git .

# Вариант 2: Вручную через SCP/SFTP
# Загрузите: qr.py, requirements.txt, telegram-bot.service, deploy.sh
```

### 7. Создайте .env файл
```bash
nano .env
```
```
BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=your_telegram_id_here
OWNER_NAME=ULIANA EMELINA
ACCOUNT_NUMBER=3247217010/3030
```

### 8. Разверните бота одной командой
```bash
chmod +x deploy.sh
./deploy.sh
```

### 9. Проверьте работу
```bash
sudo systemctl status telegram-bot
sudo journalctl -u telegram-bot -f
```

## 🔧 Управление

```bash
# Просмотр логов в реальном времени
sudo journalctl -u telegram-bot -f

# Перезапуск бота
sudo systemctl restart telegram-bot

# Обновление бота (если используете git)
cd ~/telegram-bot
git pull
sudo systemctl restart telegram-bot
```

## 💰 Сравнение стоимости

| Сервис | Стоимость | Лимиты |
|--------|-----------|--------|
| **Oracle Cloud Free** | **Бесплатно навсегда** | 1GB RAM, 1/8 CPU |
| Railway | $5/месяц | ~500MB RAM |
| Heroku | $7/месяц | 512MB RAM |
| DigitalOcean | $6/месяц | 1GB RAM |
| AWS EC2 | $3.5/месяц | 1GB RAM (12 месяцев) |

## ⚠️ Важные моменты

1. **Карта нужна только для верификации** - списаний не будет
2. **Always Free навсегда** - нет временных ограничений  
3. **Инстанс может быть остановлен** при длительном простое (30+ дней)
4. **Делайте бэкапы** важных данных
5. **Мониторьте использование** ресурсов

## 🆚 Oracle Cloud vs Railway

**Плюсы Oracle:**
- ✅ Бесплатно навсегда
- ✅ Больше ресурсов (1GB vs 500MB RAM)
- ✅ Полный root доступ
- ✅ Можно устанавливать любое ПО

**Минусы Oracle:**
- ❌ Более сложная настройка
- ❌ Нужна карта для регистрации
- ❌ Может потребоваться администрирование Linux

**Плюсы Railway:**
- ✅ Простое развертывание
- ✅ Git интеграция из коробки
- ✅ Не нужна карта

**Минусы Railway:**
- ❌ Платно ($5/месяц)
- ❌ Меньше ресурсов
- ❌ Ограниченная кастомизация

## 🎯 Рекомендация

**Используйте Oracle Cloud если:**
- Хотите бесплатное решение
- Не боитесь Linux администрирования
- Нужно больше ресурсов

**Оставайтесь на Railway если:**
- Цените простоту
- $5/месяц не проблема
- Не хотите заниматься настройкой сервера
