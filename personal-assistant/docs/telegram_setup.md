# Telegram Bot Setup Guide

## Overview

The AI Personal Assistant can be accessed via Telegram bot. This guide explains how to set up and configure the Telegram integration.

## Prerequisites

1. A Telegram account
2. The backend service running (via Docker or locally)
3. A publicly accessible URL for webhook (or use polling alternative)

## Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create your bot:
   - Choose a name for your bot (e.g., "My AI Assistant")
   - Choose a username for your bot (must end in 'bot', e.g., "my_ai_assistant_bot")
4. BotFather will provide you with a **BOT TOKEN** (keep this secret!)

Example token format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

## Step 2: Configure Environment Variables

Edit your `backend/.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
```

**Important:** 
- Never commit your `.env` file to version control
- The webhook URL must be publicly accessible (use ngrok for local development)

## Step 3: Set Up Webhook (Production)

For production, you need a publicly accessible URL:

### Option A: Using a Domain

If you have a domain pointing to your server:

```bash
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
```

### Option B: Using ngrok (Development)

1. Install ngrok: https://ngrok.com/download
2. Start ngrok:
   ```bash
   ngrok http 8000
   ```
3. Copy the HTTPS URL provided by ngrok
4. Update your `.env`:
   ```bash
   TELEGRAM_WEBHOOK_URL=https://xxxx-xxxx.ngrok.io/api/v1/telegram/webhook
   ```

## Step 4: Start the Application

### Using Docker

```bash
cd personal-assistant/docker
docker-compose up -d
```

### Set the Webhook

Once the application is running, set up the webhook:

```bash
curl -X POST http://localhost:8000/api/v1/telegram/set-webhook
```

Or if using ngrok/domain:

```bash
curl -X POST https://your-domain.com/api/v1/telegram/set-webhook
```

### Verify Webhook

Check webhook status:

```bash
curl http://localhost:8000/api/v1/telegram/webhook-info
```

## Step 5: Test Your Bot

1. Open Telegram
2. Search for your bot by username (e.g., `@my_ai_assistant_bot`)
3. Start a conversation with `/start`
4. Try commands like:
   - "Create a task to finish the API documentation tomorrow"
   - "What meetings do I have tomorrow?"
   - "Summarize my recent tasks"

## Alternative: Polling Mode (Development Only)

If you can't set up a webhook, you can use polling mode by creating a simple script:

```python
# scripts/telegram_polling.py
import asyncio
import aiohttp

BOT_TOKEN = "your-bot-token"
WEBHOOK_URL = "http://localhost:8000/api/v1/telegram/webhook"

async def poll():
    offset = 0
    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"offset": offset, "timeout": 30}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                result = await resp.json()
                
        for update in result.get("result", []):
            offset = max(offset, update["update_id"] + 1)
            
            # Forward to webhook
            async with aiohttp.ClientSession() as session:
                await session.post(WEBHOOK_URL, json=update)
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(poll())
```

## Troubleshooting

### Bot doesn't respond

1. Check if the webhook is set correctly:
   ```bash
   curl http://localhost:8000/api/v1/telegram/webhook-info
   ```

2. Verify the bot token in `.env` is correct

3. Check backend logs for errors:
   ```bash
   docker-compose logs -f backend
   ```

### Webhook fails to set

1. Ensure your webhook URL is publicly accessible
2. Make sure port 8000 is open
3. Verify SSL certificate if using HTTPS

### "Telegram bot not configured" error

Ensure `TELEGRAM_BOT_TOKEN` is set in your `.env` file and the container has been restarted.

## Security Considerations

1. **Keep your bot token secret** - Never share it or commit it to version control
2. **Use HTTPS** - Always use HTTPS for webhook URLs in production
3. **Validate updates** - The webhook validates that messages come from Telegram
4. **Rate limiting** - Telegram has rate limits; implement backoff if needed

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/telegram/webhook` | POST | Receive Telegram updates |
| `/api/v1/telegram/set-webhook` | POST | Configure webhook URL |
| `/api/v1/telegram/webhook-info` | GET | Get webhook status |

## Next Steps

- Configure additional tools (calendar, email, documents)
- Set up MCP servers for extended functionality
- Customize the system prompt for your use case
- Implement user authentication for multi-user support
