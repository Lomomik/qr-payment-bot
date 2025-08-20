# QR Payment Bot - Deployment Guide

## Deploy to Render (Recommended)

1. Fork this repository to your GitHub
2. Go to [render.com](https://render.com) and sign up
3. Connect your GitHub account
4. Create new "Web Service"
5. Select this repository
6. Configure:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python qr.py
   ```
7. Add environment variables:
   - BOT_TOKEN (your telegram bot token)
   - ADMIN_TELEGRAM_ID (your telegram user id)
   - OWNER_NAME (ULIANA EMELINA)
   - ACCOUNT_NUMBER (3247217010/3030)

## Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Connect GitHub and select this repo
3. Add environment variables in settings
4. Deploy automatically

## Deploy to PythonAnywhere

1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload files via Files tab
3. Go to Web tab and create new app
4. Set startup file to qr.py
5. Add environment variables in .env file

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env file
BOT_TOKEN=your_bot_token
ADMIN_TELEGRAM_ID=your_id
OWNER_NAME=ULIANA EMELINA
ACCOUNT_NUMBER=3247217010/3030

# Run bot
python qr.py
```
