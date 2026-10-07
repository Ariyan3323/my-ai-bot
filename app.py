import os
import threading
import time
import gradio as gr

BOT_VERSION = os.environ.get("SAM_BUILD", "2026-10-07-bugfix-2")
_bot_state = {
    "running": False,
    "last_error": "",
    "restarts": 0,
}

def run_telegram_bot():
    """Run Telegram polling in a supervised thread and restart after crashes."""
    while True:
        try:
            from bot import bot, BOT_VERSION as CODE_BUILD
            _bot_state["running"] = False
            _bot_state["last_error"] = ""
            print(f"[SAM] Telegram supervisor starting. Build={CODE_BUILD}", flush=True)

            # Long polling and webhook mode are mutually exclusive.
            bot.remove_webhook()
            _bot_state["running"] = True
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=False,
                allowed_updates=["message", "callback_query"]
            )
            print("[SAM] Telegram polling stopped unexpectedly; restarting...", flush=True)

        except Exception as e:
            _bot_state["running"] = False
            _bot_state["last_error"] = repr(e)
            _bot_state["restarts"] += 1
            print(f"[SAM] Telegram polling crashed: {e!r}", flush=True)

        time.sleep(3)

threading.Thread(target=run_telegram_bot, daemon=True, name="telegram-supervisor").start()

def get_bot_status():
    return (
        f"🟢 SAM Space is running\n"
        f"🧩 Build: {BOT_VERSION}\n"
        f"🤖 Telegram worker: {'RUNNING' if _bot_state['running'] else 'RESTARTING/STOPPED'}\n"
        f"🔁 Worker restarts: {_bot_state['restarts']}\n"
        f"⚠️ Last error: {_bot_state['last_error'] or 'none'}"
    )

with gr.Blocks(title="SAM AI Bot") as demo:
    gr.Markdown("# 🤖 SAM AI Bot")
    status_text = gr.Textbox(value=get_bot_status(), label="وضعیت زنده ربات", interactive=False)
    refresh_btn = gr.Button("🔄 بروزرسانی وضعیت")
    refresh_btn.click(fn=get_bot_status, outputs=status_text)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
