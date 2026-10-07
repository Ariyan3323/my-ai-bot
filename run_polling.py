"""
Entry point for running the bot with long-polling instead of a webhook.

Use this when there is no public HTTPS URL for Telegram to send updates to
(e.g. running on a phone via Termux, or on a local machine). This does NOT
require WEBHOOK_URL to be set - only TELEGRAM_TOKEN and GEMINI_API_KEY.

Run with:
    python run_polling.py
"""
import os
from bot import bot, BOT_VERSION  # importing bot.py registers all @bot.message_handler routes

if __name__ == "__main__":
    # Make sure no webhook is set, otherwise Telegram will refuse to let
    # this process poll for updates (409 Conflict).
    bot.remove_webhook()
    print(f"Sam is running in polling mode. Build: {BOT_VERSION}")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
