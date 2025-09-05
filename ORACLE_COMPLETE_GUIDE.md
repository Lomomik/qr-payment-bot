# 🎯 Oracle Cloud Always Free - Полная инструкция

Развертывание Telegram бота для QR платежей на **бесплатном навсегда** сервере Oracle Cloud.

## 📋 Что вам понадобится

- Аккаунт Oracle Cloud (бесплатная регистрация)
- Кредитная карта для верификации (списаний не будет!)
- 30-60 минут времени для первоначальной настройки

## 🚀 Пошаговая инструкция

### Шаг 1: Регистрация в Oracle Cloud

1. Перейдите на https://oracle.com/cloud/free/
2. Нажмите **"Start for free"**
3. Заполните форму регистрации:
   - Выберите страну (лучше США или Германия для стабильности)
   - Укажите реальные данные
   - Добавьте кредитную карту (для верификации, не спишется ни копейки)
4. Подтвердите email и телефон
5. Дождитесь активации аккаунта (может занять до 24 часов)

### Шаг 2: Создание виртуальной машины

1. Войдите в **Oracle Cloud Console**
2. В левом меню: **Compute** → **Instances**
3. Нажмите **"Create Instance"**

**Настройки инстанса:**
- **Name**: `telegram-bot-server`
- **Compartment**: оставьте по умолчанию
- **Placement**: любой Availability Domain
- **Image**: `Oracle Linux 8` (рекомендуется)
- **Shape**: 
  - Нажмите **"Change Shape"**
  - Выберите **"Always Free Eligible"**
  - `VM.Standard.E2.1.Micro` (1/8 OCPU, 1GB RAM)
- **Primary VNIC**: оставьте настройки по умолчанию
- **SSH Keys**: 
  - Выберите **"Generate SSH Key Pair"**
  - Нажмите **"Save Private Key"** и **"Save Public Key"**
  - **ОБЯЗАТЕЛЬНО сохраните приватный ключ!**

4. Нажмите **"Create"**
5. Дождитесь создания инстанса (2-5 минут)
6. **Запишите публичный IP адрес** инстанса

### Шаг 3: Настройка сетевой безопасности

1. В консоли перейдите: **Networking** → **Virtual Cloud Networks**
2. Нажмите на VCN вашего инстанса
3. Слева выберите **"Security Lists"**
4. Нажмите на **"Default Security List for vcn-..."**
5. Нажмите **"Add Ingress Rules"**

**Добавьте правило:**
- **Source Type**: CIDR
- **Source CIDR**: `0.0.0.0/0`
- **IP Protocol**: TCP
- **Destination Port Range**: `80,443,8080`
- **Description**: `HTTP HTTPS Bot`

6. Нажмите **"Add Ingress Rules"**

### Шаг 4: Подключение к серверу

**Из Windows (PowerShell):**
```powershell
# Если у вас Windows 10+ с OpenSSH
ssh -i C:\path\to\your\private\key opc@YOUR_PUBLIC_IP

# Замените YOUR_PUBLIC_IP на реальный IP вашего сервера
```

**Если OpenSSH не установлен:**
1. Скачайте PuTTY: https://putty.org/
2. Конвертируйте ключ в формат .ppk через PuTTYgen
3. Подключитесь через PuTTY

### Шаг 5: Автоматическая настройка сервера

После подключения выполните:

```bash
# Скачивание и запуск скрипта настройки
curl -fsSL https://raw.githubusercontent.com/Lomomik/qr-payment-bot/main/setup_oracle_server.sh -o setup.sh
chmod +x setup.sh
./setup.sh
```

Или настройте вручную:

```bash
# Обновление системы
sudo dnf update -y

# Установка Python и зависимостей
sudo dnf install python39 python39-pip git nano htop -y

# Создание символических ссылок
sudo alternatives --install /usr/bin/python python /usr/bin/python3.9 1
sudo alternatives --install /usr/bin/pip pip /usr/bin/pip3.9 1

# Настройка firewall
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload

# Создание директории проекта
mkdir -p ~/telegram-bot
cd ~/telegram-bot
```

### Шаг 6: Загрузка файлов бота

**Вариант 1: Через Git (рекомендуется)**
```bash
cd ~/telegram-bot
git clone https://github.com/Lomomik/qr-payment-bot.git .
```

**Вариант 2: Загрузка файлов вручную**

Используйте WinSCP, FileZilla или scp для загрузки файлов:
- `qr.py`
- `requirements.txt`
- `telegram-bot.service`
- `deploy.sh`
- `monitor.py`

```bash
# Пример через scp из Windows
scp -i C:\path\to\private\key qr.py opc@YOUR_PUBLIC_IP:~/telegram-bot/
scp -i C:\path\to\private\key requirements.txt opc@YOUR_PUBLIC_IP:~/telegram-bot/
# ... остальные файлы
```

### Шаг 7: Настройка переменных окружения

```bash
cd ~/telegram-bot
nano .env
```

Содержимое файла `.env`:
```
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_TELEGRAM_ID=your_telegram_user_id
OWNER_NAME=ULIANA EMELINA
ACCOUNT_NUMBER=3247217010/3030
```

**Как получить данные:**
- `BOT_TOKEN`: от [@BotFather](https://t.me/botfather) в Telegram
- `ADMIN_TELEGRAM_ID`: ваш ID от [@userinfobot](https://t.me/userinfobot)

### Шаг 8: Развертывание бота

```bash
# Делаем скрипт исполняемым
chmod +x deploy.sh

# Запускаем автоматическое развертывание
./deploy.sh
```

Скрипт автоматически:
- Создаст виртуальное окружение
- Установит зависимости
- Настроит systemd сервис
- Запустит бота

### Шаг 9: Проверка работы

```bash
# Проверка статуса сервиса
sudo systemctl status telegram-bot

# Просмотр логов в реальном времени
sudo journalctl -u telegram-bot -f

# Запуск мониторинга ресурсов
python monitor.py
```

**Проверьте бота в Telegram** - он должен отвечать на команды!

## 🔧 Управление ботом

### Основные команды

```bash
# Перезапуск бота
sudo systemctl restart telegram-bot

# Остановка бота
sudo systemctl stop telegram-bot

# Запуск бота
sudo systemctl start telegram-bot

# Просмотр логов (последние 50 строк)
sudo journalctl -u telegram-bot --no-pager -n 50

# Мониторинг ресурсов
python ~/telegram-bot/monitor.py
```

### Обновление бота

```bash
cd ~/telegram-bot
git pull  # если используете git
sudo systemctl restart telegram-bot
```

### Просмотр логов ошибок

```bash
# Логи бота
sudo journalctl -u telegram-bot -f

# Системные логи
sudo journalctl -xe

# Логи firewall
sudo journalctl -u firewalld
```

## 📊 Мониторинг

Используйте скрипт `monitor.py` для отслеживания:
- Использования CPU и памяти
- Свободного места на диске
- Статуса бота
- Сетевого трафика

```bash
# Запуск мониторинга
python monitor.py

# Добавление в cron для регулярной проверки
echo "*/5 * * * * python /home/opc/telegram-bot/monitor.py >> /home/opc/monitor.log" | crontab -
```

## 💰 Преимущества Oracle Cloud Always Free

| Параметр | Oracle Cloud Free | Railway ($5) | Heroku ($7) |
|----------|-------------------|--------------|-------------|
| **Стоимость** | **Бесплатно навсегда** | $5/месяц | $7/месяц |
| **RAM** | **1 GB** | ~500 MB | 512 MB |
| **CPU** | 1/8 OCPU | Shared | Shared |
| **Хранилище** | **200 GB** | Ограничено | Эфемерное |
| **Время работы** | **24/7** | 24/7 | 24/7 |
| **Root доступ** | **✅ Да** | ❌ Нет | ❌ Нет |
| **Кастомизация** | **✅ Полная** | ❌ Ограничена | ❌ Ограничена |

## ⚠️ Важные замечания

### Ограничения Always Free

1. **Карта нужна только для верификации** - реальных списаний не будет
2. **Инстанс может быть остановлен** при простое 30+ дней без активности
3. **Аккаунт может быть заблокирован** при подозрительной активности
4. **Один инстанс на аккаунт** в Always Free тире

### Как избежать блокировки

1. **Используйте реальные данные** при регистрации
2. **Не создавайте несколько аккаунтов** с одной карты
3. **Регулярно заходите** в консоль Oracle Cloud
4. **Мониторьте использование** ресурсов
5. **Делайте бэкапы** важных данных

### Рекомендации по безопасности

```bash
# Обновляйте систему регулярно
sudo dnf update -y

# Настройте fail2ban для защиты SSH
sudo dnf install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Измените SSH порт (опционально)
sudo nano /etc/ssh/sshd_config
# Раскомментируйте и измените: Port 2222
sudo systemctl restart sshd
```

## 🆘 Решение проблем

### Бот не отвечает
```bash
# Проверьте статус
sudo systemctl status telegram-bot

# Проверьте логи
sudo journalctl -u telegram-bot -n 20

# Проверьте .env файл
cat .env

# Перезапустите бота
sudo systemctl restart telegram-bot
```

### Нет места на диске
```bash
# Проверьте использование диска
df -h

# Очистите логи
sudo journalctl --vacuum-time=7d

# Очистите кэш пакетов
sudo dnf clean all
```

### Высокое использование памяти
```bash
# Проверьте процессы
htop

# Перезапустите бота
sudo systemctl restart telegram-bot

# Проверьте мониторинг
python monitor.py
```

## 🎯 Следующие шаги

1. **Настройте домен** (опционально) для красивого URL
2. **Добавьте HTTPS** с Let's Encrypt
3. **Настройте автобэкапы** в Object Storage
4. **Добавьте мониторинг** с уведомлениями
5. **Масштабируйте** при необходимости

## 🤝 Поддержка

Если возникли проблемы:
1. Проверьте логи: `sudo journalctl -u telegram-bot -f`
2. Перезапустите сервис: `sudo systemctl restart telegram-bot`
3. Проверьте мониторинг: `python monitor.py`
4. Обратитесь к документации Oracle Cloud

**Ваш Telegram бот теперь работает 24/7 совершенно бесплатно! 🎉**
