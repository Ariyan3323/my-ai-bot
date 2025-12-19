import os
import re
from flask import Flask, request, jsonify
import telebot
from telebot import types

# 🔌 وارد کردن ماژول‌های خدماتی
from services.tutor import handle_tutor_request
from services.writer import handle_writing_request
from services.legal import handle_legal_request
from services.trader import handle_trader_request
from services.ethics import is_ethical_request, get_ethics_rejection_message
from services.premium import check_access_level, get_premium_features

# 🔑 تنظیمات اولیه
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("لطفاً متغیر محیطی BOT_TOKEN را در Railway تنظیم کنید.")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # مثلاً: https://my-ai-bot.up.railway.app

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 🧠 حالت‌های تعاملی (برای پردازش چندمرحله‌ای)
user_states = {}

def detect_language(text: str) -> str:
    """
    تشخیص سادهٔ زبان کاربر بر اساس محتوای پیام.
    خروجی: کد زبان ('fa', 'en', 'ar')
    """
    if not text or not isinstance(text, str):
        return "fa"
    
    text_lower = text.lower()
    
    # تشخیص انگلیسی (وجود حروف انگلیسی + کلمات رایج)
    if re.search(r"[a-z]", text_lower):
        english_indicators = ["hello", "hi", "buy", "sell", "market", "price", "analysis", "btc", "eth", "crypto", "trading"]
        if any(ind in text_lower for ind in english_indicators):
            return "en"
    
    # تشخیص عربی (وجود حروف عربی یا کلمات رایج)
    if any(char in text for char in "مرحبا سلام شكر شكرا السوق تحليل شراء بيع"):
        return "ar"
    
    # پیش‌فرض: فارسی
    return "fa"

def send_disclaimer(chat_id, lang="fa"):
    messages = {
        "fa": (
            "⚠️ **هشدار حقوقی و اخلاقی**\n"
            "تمام خدمات این ربات **فقط جنبهٔ آموزشی و اطلاع‌رسانی** دارد.\n"
            "هیچ‌یک از تحلیل‌ها، پیش‌بینی‌ها یا پیشنهادات، **وعدهٔ سود یا مشاورهٔ مالی** محسوب نمی‌شود.\n"
            "**کل مسئولیت تصمیمات ترید و استفاده از اطلاعات، بر عهدهٔ شما (کاربر)** است.\n"
            "با ادامهٔ استفاده، شما این شرایط را پذیرفته‌اید."
        ),
        "en": (
            "⚠️ **Legal & Ethical Disclaimer**\n"
            "All services are for **educational and informational purposes only**.\n"
            "No analysis, prediction, or suggestion constitutes **financial advice or profit guarantee**.\n"
            "**You (the user) bear full responsibility** for your trading decisions.\n"
            "By continuing, you accept these terms."
        ),
        "ar": (
            "⚠️ **تنويه قانوني وأخلاقي**\n"
            "جميع الخدمات لأغراض **تعليمية وإعلامية فقط**.\n"
            "لا يُعد أي تحليل أو توقع أو اقتراح **نصيحة مالية أو ضمان ربح**.\n"
            "**أنت (المستخدم) تتحمل المسؤولية الكاملة** عن قرارات التداول الخاصة بك.\n"
            "بمتابعتك، فإنك تقبل هذه الشروط."
        )
    }
    bot.send_message(chat_id, messages.get(lang, messages["fa"]), parse_mode="Markdown")

# 🎯 دستور /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    lang = detect_language(message.text)
    send_disclaimer(message.chat.id, lang)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📚 یادگیری", callback_data="tutor"),
        types.InlineKeyboardButton("✍️ نویسندگی", callback_data="writer"),
        types.InlineKeyboardButton("⚖️ حقوق ایران", callback_data="legal"),
        types.InlineKeyboardButton("📈 ترید هوشمند", callback_data="trader"),
        types.InlineKeyboardButton("💎 اشتراک ویژه", callback_data="premium")
    )
    bot.send_message(message.chat.id, "لطفاً یک گزینه انتخاب کنید:", reply_markup=markup)

# 📥 پردازش دکمه‌های Inline
@bot.callback_query_handler(func=lambda call: True)
def handle_inline(call):
    user_id = call.from_user.id
    lang = detect_language(call.message.text)
    
    if not is_ethical_request(call.data):
        bot.answer_callback_query(call.id, "درخواست غیراخلاقی!")
        return

    if call.data == "tutor":
        bot.send_message(call.message.chat.id, "لطفاً موضوع درس را بنویسید (مثلاً: ریاضی):")
        user_states[user_id] = ("tutor", lang)
    elif call.data == "writer":
        bot.send_message(call.message.chat.id, "موضوع و نوع سند (مثال: هوش مصنوعی — مقاله):")
        user_states[user_id] = ("writer", lang)
    elif call.data == "legal":
        bot.send_message(call.message.chat.id, "نوع پرونده (طلاق، حضانت، ...):")
        user_states[user_id] = ("legal", lang)
    elif call.data == "trader":
        access = check_access_level(user_id)
        if access == "free":
            bot.send_message(call.message.chat.id, "📊 تحلیل آنی بازار (رایگان):\n• حرکت نهنگ‌ها (24h)\n• RSI عمومی\n\n💎 برای پیش‌بینی روزانه، اشتراک بخرید.")
        else:
            bot.send_message(call.message.chat.id, "لطفاً نماد سکه را وارد کنید (مثلاً: BTC):")
            user_states[user_id] = ("trader", lang)
    elif call.data == "premium":
        bot.send_message(call.message.chat.id, 
            "💎 **اشتراک ویژه (با Telegram Stars)**\n"
            "• 1000 Stars/ماه: پیش‌بینی روزانه + هشدار نهنگ\n"
            "• 2500 Stars/ماه: داده‌های خام + پروفایل هوشمند\n\n"
            "⚠️ فعلاً در دسترس نیست — به زودی!"
        )
    bot.answer_callback_query(call.id)

# 💬 پردازش پاسخ کاربر
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""
    lang = detect_language(text)
    
    # 🔒 فیلتر اخلاقی
    if not is_ethical_request(text):
        bot.reply_to(message, get_ethics_rejection_message(lang), parse_mode="Markdown")
        return

    if user_id in user_states:
        mode, _ = user_states[user_id]
        if mode == "tutor":
            response = handle_tutor_request(text)
        elif mode == "writer":
            try:
                topic, info = text.split("—", 1)
                doc_type = "مقاله" if "مقاله" in info else "پروژه"
                level = "کاری" if "کاری" in info else "دانشگاهی"
                response = handle_writing_request(topic.strip(), doc_type, level)
            except:
                response = handle_writing_request(text)
        elif mode == "legal":
            response = handle_legal_request(text)
        elif mode == "trader":
            response = handle_trader_request(text)
        else:
            response = "لطفاً از منو استفاده کنید."
        
        bot.reply_to(message, response, parse_mode="Markdown")
        del user_states[user_id]
    else:
        bot.reply_to(message, "لطفاً از منوی /start استفاده کنید.")

# 🌐 Webhook برای Railway
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Invalid', 400

@app.route('/setwebhook', methods=['GET'])
def set_webhook_route():
    if WEBHOOK_URL:
        bot.set_webhook(url=WEBHOOK_URL + "/webhook")
        return jsonify({"status": "Webhook set!"})
    return jsonify({"error": "WEBHOOK_URL not set"})

@app.route('/', methods=['GET'])
def health():
    return '🤖 Rbot is running on Railway!'

# 🚀 اجرا
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
