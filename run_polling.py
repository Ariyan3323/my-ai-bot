"""Standalone/local Telegram polling entrypoint with automatic restart."""
import time
import traceback
from bot import bot, BOT_VERSION

if __name__ == "__main__":
    print("=" * 72, flush=True)
    print(f"[SAM-LEGACY-BOOT] ENTRYPOINT=run_polling.py | BOT_BUILD={BOT_VERSION}", flush=True)
    while True:
        try:
            me = bot.get_me()
            print(f"[SAM-LEGACY-BOOT] Telegram auth OK: @{getattr(me, 'username', '')}", flush=True)
            print("[SAM-LEGACY-BOOT] Removing webhook...", flush=True)
            bot.remove_webhook()
            print("[SAM-LEGACY-BOOT] POLLING_STARTED", flush=True)
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=False, allowed_updates=["message", "callback_query", "my_chat_member"])
            print("[SAM-LEGACY-BOOT] POLLING_RETURNED; restarting...", flush=True)
        except Exception as exc:
            print(f"[SAM-LEGACY-BOOT] POLLING_CRASH: {type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
        time.sleep(3)
