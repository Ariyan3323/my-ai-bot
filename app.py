import os
import threading
import time
import subprocess
import gradio as gr

def run_telegram_bot():
    """Runs the Telegram bot in background."""
    time.sleep(2)
    print("Starting Telegram Bot via run_polling.py...")
    try:
        subprocess.run(["python", "run_polling.py"])
    except Exception as e:
        print(f"Error running bot: {e}")

# Start the Telegram bot in background thread
threading.Thread(target=run_telegram_bot, daemon=True).start()

def get_bot_status():
    token = os.environ.get("TELEGRAM_TOKEN")
    if token:
        masked = token[:6] + "..." + token[-4:]
        return f"🟢 سرور ابری فعال است | ربات تلگرام با توکن ({masked}) متصل شد."
    return "🟡 سرور فعال است اما متغیر TELEGRAM_TOKEN در بخش Settings > Variables تنظیم نشده است."

with gr.Blocks(title="Sam AI Bot") as demo:
    gr.Markdown("# 🤖 سرور ابری ۲۴ ساعته ربات هوش مصنوعی Sam")
    gr.Markdown("این سرور در هاگینگ‌فیس به صورت رایگان و پیوسته فعال است و پیام‌های تلگرام را در لحظه دریافت و پاسخ می‌دهد.")
    status_text = gr.Textbox(value=get_bot_status(), label="وضعیت ربات", interactive=False)
    refresh_btn = gr.Button("🔄 بروزرسانی وضعیت")
    refresh_btn.click(fn=get_bot_status, outputs=status_text)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
