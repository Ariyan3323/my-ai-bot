import os
import telebot
from telebot import types

# 🔌 وارد کردن ماژول‌ها
from services.tutor import handle_tutor_request
from services.writer import handle_writing_request
from services.legal import handle_legal_request
from services.trader import handle_trader_request
from services.ethics import is_ethical_request, get_ethics_rejection_message

# 🔑 دریافت توکن از متغیر محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("لطفاً متغیر محیطی BOT_TOKEN را در Railway تنظیم کنید.")

bot = telebot.TeleBot(BOT_TOKEN)

# 🧠 حالت‌های تعاملی (برای پردازش چندمرحله‌ای)
user_states = {}

# 🎯 دستور /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add("📚 معلم خصوصی", "✍️ مقاله / پروژه")
    markup.add("⚖️ حقوقی ایران", "📈 آموزش ترید")
    markup.add("💰 اشتراک ماهانه")
    
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
    bot.reply_to(message, "لطفاً از منوی زیر یک گزینه انتخاب کنید.")

# 💬 پاسخ به دکمه‌ها و پیام‌ها
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # 🔒 بررسی اخلاقی بودن درخواست
    if not is_ethical_request(text):
        rejection_message = get_ethics_rejection_message()
        bot.reply_to(message, rejection_message, parse_mode="Markdown")
        return

    if text == "📚 معلم خصوصی":
        bot.reply_to(message, "لطفاً موضوع درس را بنویسید (مثلاً: ریاضی، فیزیک، زبان):")
        user_states[user_id] = "tutor_subject"

    elif text == "✍️ مقاله / پروژه":
        bot.reply_to(message, "لطفاً موضوع و نوع سند را بنویسید (مثال: «هوش مصنوعی — مقاله دانشگاهی»):")
        user_states[user_id] = "writer_request"

    elif text == "⚖️ حقوقی ایران":
        bot.reply_to(message, "لطفاً نوع پرونده را بنویسید (مثال: طلاق، حضانت، اجاره، کارگری):")
        user_states[user_id] = "legal_case"

    elif text == "📈 آموزش ترید":
        bot.reply_to(message, "لطفاً موضوع آموزش را انتخاب کنید:\nتحلیل تکنیکال\nروانشناسی\nمدیرییت سرمایه\non-chain")
        user_states[user_id] = "trader_topic"

    elif text == "💰 اشتراک ماهانه":
        bot.reply_to(message, "این بخش به زودی با پشتیبانی از Telegram Stars فعال می‌شود. 🌟")

    else:
        # پردازش پاسخ‌های ارسالی توسط کاربر
        state = user_states.get(user_id)
        if state == "tutor_subject":
            response = handle_tutor_request(text)
            bot.reply_to(message, response, parse_mode="Markdown")
            del user_states[user_id]

        elif state == "writer_request":
            try:
                topic, doc_info = text.split("—", 1)
                doc_type = "مقاله"
                level = "دانشگاهی"
                if "پروژه" in doc_info:
                    doc_type = "پروژه"
                if "کاری" in doc_info:
                    level = "کاری"
                response = handle_writing_request(topic.strip(), doc_type, level)
            except:
                response = handle_writing_request(text)
            bot.reply_to(message, response, parse_mode="Markdown")
            del user_states[user_id]

        elif state == "legal_case":
            response = handle_legal_request(text)
            bot.reply_to(message, response, parse_mode="Markdown")
            del user_states[user_id]

        elif state == "trader_topic":
            response = handle_trader_request(text)
            bot.reply_to(message, response, parse_mode="Markdown")
            del user_states[user_id]

        else:
            bot.reply_to(message, "لطفاً از منوی زیر استفاده کنید.")

# 🚀 شروع ربات
if __name__ == "__main__":
    print("ربات در حال اجراست... (مستقر در Railway)")
    bot.infinity_polling()
