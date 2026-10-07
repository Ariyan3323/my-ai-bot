import os
import threading
import time
import traceback
import gradio as gr

APP_BUILD = "2026-10-07-deploy-debug-1"
_bot_state = {"running": False, "last_error": "", "restarts": 0, "started_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "bot_identity": ""}

def run_telegram_bot():
    while True:
        try:
            from bot import bot, BOT_VERSION as CODE_BUILD
            print("=" * 72, flush=True)
            print(f"[SAM-BOOT] ENTRYPOINT=app.py | APP_BUILD={APP_BUILD}", flush=True)
            print(f"[SAM-BOOT] BOT_BUILD={CODE_BUILD}", flush=True)
            print("[SAM-BOOT] Telegram worker initializing...", flush=True)
            _bot_state["running"] = False
            _bot_state["last_error"] = ""
            me = bot.get_me()
            _bot_state["bot_identity"] = f"@{me.username}" if getattr(me, "username", None) else str(me.id)
            print(f"[SAM-BOOT] Telegram auth OK: {_bot_state['bot_identity']}", flush=True)
            print("[SAM-BOOT] Removing Telegram webhook...", flush=True)
            bot.remove_webhook()
            print("[SAM-BOOT] Webhook removed. Starting infinity_polling...", flush=True)
            _bot_state["running"] = True
            print("[SAM-BOOT] POLLING_STARTED", flush=True)
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=False, allowed_updates=["message", "callback_query", "my_chat_member"])
            _bot_state["running"] = False
            print("[SAM-BOOT] POLLING_RETURNED; supervisor will restart it.", flush=True)
        except Exception as e:
            _bot_state["running"] = False
            _bot_state["last_error"] = f"{type(e).__name__}: {e}"
            _bot_state["restarts"] += 1
            print(f"[SAM-BOOT] POLLING_CRASH: {_bot_state['last_error']}", flush=True)
            traceback.print_exc()
        time.sleep(3)

def heartbeat():
    while True:
        time.sleep(60)
        print(f"[SAM-HEARTBEAT] worker={'RUNNING' if _bot_state['running'] else 'STOPPED'} restarts={_bot_state['restarts']} bot={_bot_state['bot_identity'] or 'unknown'}", flush=True)

threading.Thread(target=run_telegram_bot, daemon=True, name="telegram-supervisor").start()
threading.Thread(target=heartbeat, daemon=True, name="sam-heartbeat").start()

def get_bot_status():
    return ("🟢 SAM Space is running\n"
            f"🧩 App Build: {APP_BUILD}\n"
            f"🤖 Telegram bot: {_bot_state.get('bot_identity') or 'loading'}\n"
            f"📡 Telegram worker: {'RUNNING' if _bot_state['running'] else 'STOPPED/RESTARTING'}\n"
            f"🔁 Worker restarts: {_bot_state['restarts']}\n"
            f"⚠️ Last error: {_bot_state['last_error'] or 'none'}\n"
            f"⏱️ Started: {_bot_state['started_at']}")

with gr.Blocks(title="SAM AI Bot") as demo:
    gr.Markdown("# 🤖 SAM AI Bot")
    status_text = gr.Textbox(value=get_bot_status(), label="وضعیت زنده ربات", interactive=False)
    refresh_btn = gr.Button("🔄 بروزرسانی وضعیت")
    refresh_btn.click(fn=get_bot_status, outputs=status_text)

if __name__ == "__main__":
    print(f"[SAM-BOOT] MAIN_START app.py | APP_BUILD={APP_BUILD}", flush=True)
    demo.launch(server_name="0.0.0.0", server_port=7860)
