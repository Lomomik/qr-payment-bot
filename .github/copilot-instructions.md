# QR Payment Bot - AI Coding Agent Instructions

## Project Overview
This is a Telegram bot for Czech beauty salon that generates QR codes for payments. It integrates with Czech banking apps (Air Bank, Raiffeisenbank CZ) using the SPD payment format standard.

## Core Architecture

### Main Files
- `qr.py` - Production bot with emoji-categorized services and amount selection buttons
- `qr_test.py` - Testing version (loads `.env.test`, identical functionality)
- `.env` - Production config (BOT_TOKEN, ADMIN_TELEGRAM_ID, OWNER_NAME, ACCOUNT_NUMBER)
- `.env.test` - Test bot configuration

### Critical QR Format
The bot generates Czech banking QR codes using exact SPD format:
```
SPD*1.0*ACC:{IBAN}*RN:{OWNER_NAME.upper()}*AM:{formatted_amount}*CC:CZK*MSG:{service}
```
**Never modify this format** - it's tested with Czech banks. Amount formatting uses commas for decimals (Czech standard).

### State Management Pattern
Bot uses `context.user_data` for conversation flow:
```python
# State flags
context.user_data['waiting_for_amount'] = True
context.user_data['waiting_for_service'] = True
context.user_data['amount'] = amount  # Store selected amount
```

### Service Categories (Emoji System)
Services are organized by emoji prefixes for visual grouping:
- 🌿 - Eyebrow services (ÚPRAVA, BARVENÍ, etc.)
- 👁️ - Basic lash services (LAMINACE ŘAS, BARVENÍ ŘAS)
- ✨ - Combined services (lash + brow combinations)
- 👄 - Beauty/styling (LÍČENÍ, ÚČES)

**Important**: When adding services, follow this emoji categorization and maintain Czech language.

## Key Development Patterns

### Keyboard Layouts
1. **Amount Selection**: 3 buttons per row (500-1800 CZK range), plus "✏️ Ввести свою сумму"
2. **Service Selection**: First services single-row, last 4 services in 2x2 grid
3. **Main Menu**: Persistent bottom keyboard with 3 core functions

### Error Handling
- Amount validation: 0 < amount <= 1,000,000 CZK
- Parse errors show specific format examples
- State validation prevents out-of-order interactions

### Callback Data Patterns
- `amount_{value}` - Amount selection buttons
- `amount_custom` - Custom amount input trigger  
- `service_{key}` - Service selection
- `service_none` - No service specified

### Text Formatting
Use HTML parse mode (`parse_mode='HTML'`) with `<b>` tags for better Telegram compatibility than Markdown.

## Development Workflows

### Testing Changes
1. Modify `qr_test.py` first 
2. Test with `.env.test` bot token
3. Apply changes to `qr.py` when validated
4. Deploy via git push (Railway auto-deploys from main branch)

### Adding New Services
1. Add to `SERVICES` dict with appropriate emoji prefix
2. Use Czech language for service names
3. Test QR generation to ensure service appears in payment message

### Environment Setup
```bash
pip install python-telegram-bot==21.4 qrcode[pil]==7.4.2 python-dotenv==1.0.1
```

### Deployment
- **Production**: Railway auto-deploys from GitHub main branch
- **Alternative**: Oracle Cloud Always Free (see ORACLE_* docs)
- **Local**: `python qr.py` or `python qr_test.py`

## Critical Considerations

### Banking Integration
- QR format is Czech banking standard - tested with Air Bank & Raiffeisenbank CZ
- Amount formatting uses European decimal notation (comma as decimal separator)
- IBAN is hardcoded for specific salon account

### Multi-language Context
- UI uses Russian for staff (salon employees)
- Services use Czech (banking/payment context)
- Comments/logs in Russian for staff understanding

### State Flow
Payment creation: Amount selection → Service selection → QR generation
Each step validates previous state to prevent errors.

## Common Modifications

When adding features, preserve the emoji categorization system and Czech banking format. Test with `qr_test.py` before deploying to production.
