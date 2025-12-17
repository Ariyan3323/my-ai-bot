import os
from services.tutor import handle_tutor_request
from services.writer import handle_writing_request
from services.legal import handle_legal_request
from services.trader import handle_trader_request
import telebot
from telebot import types

# 🔑 دریافت توکن از متغیر محیطی (برای امنیت)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("لطفاً متغیر محیطی BOT_TOKEN را در Railway تنظیم کنید.")

bot = telebot.TeleBot(BOT_TOKEN)

# 🎯 دستور /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton("📚 معلم خصوصی")
    btn2 = types.KeyboardButton("✍️ مقاله / پروژه")
    btn3 = types.KeyboardButton("⚖️ حقوقی ایران")
    btn4 = types.KeyboardButton("📈 آموزش ترید")
    btn5 = types.KeyboardButton("💰 اشتراک ماهانه")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    
    welcome_msg = (
        "سلام! من ربات هوشمند شما هستم.\n\n"
        "من می‌تونم کمکتون کنم در:\n"
        "• یادگیری دروس (ریاضی، فیزیک، زبان و ...)\n"
        "• نوشتن مقاله، پروژه یا پایان‌نامه\n"
        "• تهیه لایحه حقوقی (طلاق، حضانت، کارگری، اجاره)\n"
        "• آموزش ترید و تحلیل بازار\n\n"
        "برای شروع، یکی از دکمه‌های زیر رو بزنید 👇"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

# 📚 راهنما
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "برای شروع، از منوی زیر یک گزینه انتخاب کنید.")

# 💬 پاسخ به دکمه‌ها
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text
    if text == "📚 معلم خصوصی":
        # 📚 ماژول معلم خصوصی
        response = handle_tutor_request("ریاضی") # شروع با یک درس پیش‌فرض
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
    elif text == "✍️ مقاله / پروژه":
        # ✍️ ماژول نویسنده
        response = handle_writing_request("هوش مصنوعی", "مقاله", "دانشگاهی") # شروع با یک موضوع پیش‌فرض
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
    elif text == "⚖️ حقوقی ایران":
        # ⚖️ ماژول حقوقی
        response = handle_legal_request("طلاق") # شروع با یک موضوع پیش‌فرض
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
    elif text == "📈 آموزش ترید":
        # 📈 ماژول ترید
        response = handle_trader_request("تحلیل تکنیکال") # شروع با یک موضوع پیش‌فرض
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
    elif text == "💰 اشتراک ماهانه":
        # 🔮 اینجا ماژول Stars فعال می‌شه (بعداً)
        bot.reply_to(message, "اشتراک ماهانه شامل دسترسی به همه خدمات پیشرفته است.\nدر حال حاضر در دسترس نیست — به زودی فعال می‌شود.")
    else:
        bot.reply_to(message, "لطفاً از منوی زیر استفاده کنید.")

# 🚀 شروع ربات
if __name__ == "__main__":
    print("ربات در حال اجراست... (مستقر در Railway)")
    bot.infinity_polling()
