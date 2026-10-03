import os
import json
from dotenv import load_dotenv
from telebot import TeleBot, types
from google import genai
from google.genai import types as gemini_types
from google.genai.errors import APIError

# Import Service Modules
from services.ethics import is_ethical_request, get_ethics_rejection_message
from services.trader import handle_trader_request
from services.legal import handle_legal_request
from services.tutor import handle_tutor_request
from services.writer import handle_writing_request
from services.premium import check_access_level, get_premium_features
from services.image_generator import handle_image_request
from services.admin import is_verified, show_auth_buttons, is_mohammad, handle_admin_dashboard, set_user_level, get_user_list, ADMIN_ID
from services.memory import add_to_memory, get_history, handle_personality_analysis, get_personality
from services.voice import text_to_voice, handle_voice_settings
from services.self_improve import grok_search, self_upgrade, check_autonomy, update_resources_limit, hardware_stress_test, system_guardian, track_hacker, profit_hunter

# ----------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------
load_dotenv()

# Telegram and Gemini API Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("Error: TELEGRAM_TOKEN or GEMINI_API_KEY not found in environment variables.")

bot = TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)
model_name = "gemini-flash-latest"

# Map function names to actual functions for execution
tool_functions = {
    "handle_trader_request": handle_trader_request,
    "handle_legal_request": handle_legal_request,
    "handle_tutor_request": handle_tutor_request,
    "handle_writing_request": handle_writing_request,
    "handle_image_request": handle_image_request,
    "handle_admin_dashboard": handle_admin_dashboard,
    "handle_personality_analysis": handle_personality_analysis,
    "grok_search": grok_search,
    "check_autonomy": check_autonomy,
    "update_resources_limit": update_resources_limit,
    "hardware_stress_test": hardware_stress_test,
    "system_guardian": system_guardian,
    "track_hacker": track_hacker,
    "profit_hunter": profit_hunter,
    "set_user_level": set_user_level,
    "get_user_list": get_user_list,
    "check_access_level": check_access_level,
    "get_premium_features": get_premium_features,
}

# ----------------------------------------------------------------------
# 2. Core Agent Logic (Function Calling)
# ----------------------------------------------------------------------

def get_gemini_response(message):
    """Sends prompt to Gemini and handles function calls."""
    
    user_id = message.from_user.id
    user_prompt = message.text.strip()
    
    # All service functions are passed as tools to the model
    tools = [
        handle_trader_request,
        handle_legal_request,
        handle_tutor_request,
        handle_writing_request,
        handle_image_request,
        handle_admin_dashboard,
        handle_personality_analysis,
        grok_search,
        check_autonomy,
        update_resources_limit,
        hardware_stress_test,
        system_guardian,
        track_hacker,
        profit_hunter,
        set_user_level,
        get_user_list,
        check_access_level,
        get_premium_features,
    ]
    
    # Add memory to the prompt for context
    user_history = get_history(message.from_user.id)
    
    # Use the prompt with history for the model
    full_prompt = user_prompt
    if user_history:
        full_prompt = f"سابقه مکالمه کاربر:\n{user_history}\n\nدرخواست جدید: {user_prompt}"
    
    user_personality = get_personality(message.from_user.id)
    
    # Update System Instruction with new context
    system_instruction = (
        "You are a Super-Agent for the Iranian market, specialized in trading, "
        "Iranian law, academic tutoring, and professional writing. "
        "Your primary language is Farsi (Persian). "
        "The user's personality is analyzed as: "
        f"'{user_personality}'. Respond in a way that is tailored to this personality. "
        "Use the provided tools to answer specific user requests. "
        "If a tool is available, you MUST use it. If no tool is relevant, "
        "answer the user's question directly in Farsi."
    )

    # Use generate_content for a single turn with tools
    response = client.models.generate_content(
        model=model_name,
        contents=full_prompt,
        config=gemini_types.GenerateContentConfig(
            tools=None,
            system_instruction=system_instruction
        )
    )

    # Function Calling Loop
    while response.function_calls:
        tool_responses = []
        
        for function_call in response.function_calls:
            function_name = function_call.name
            args = dict(function_call.args)
            
            if function_name in tool_functions:
                # Execute the local function
                local_function = tool_functions[function_name]
                
                # Special handling for user_id in check_access_level
                if function_name == "check_access_level":
                    args["user_id"] = user_id 
                
                # Execute the function with arguments
                function_result = local_function(**args)
                
                # Prepare the tool response for the model
                tool_responses.append(
                    gemini_types.Part.from_function_response(
                        name=function_name,
                        response={"result": function_result}
                    )
                )
            else:
                # Handle unknown function call
                tool_responses.append(
                    gemini_types.Part.from_function_response(
                        name=function_name,
                        response={"error": f"Unknown function: {function_name}"}
                    )
                )

        # Send the function results back to the model
        response = client.models.generate_content(
            model=model_name,
            contents=[full_prompt, *tool_responses], # Send original prompt + tool results
            config=gemini_types.GenerateContentConfig(
                tools=None,
                system_instruction=system_instruction
            )
        )
        
    return response.text

# ----------------------------------------------------------------------
# 3. Telegram Message Handler
# ----------------------------------------------------------------------

# --- Gatekeeper Middleware ---
@bot.middleware_handler
def check_auth(message):
    """Checks if the user is verified before processing any command."""
    user_id = message.from_user.id
    
    # If the user is not verified, send the auth message and stop processing
    if not is_verified(user_id):
        # Allow /start command to pass through for initial setup
        if message.text and message.text.startswith('/start'):
            return True 
        
        # If not verified and not /start, we stop processing the message
        # The user will need to use the /start command to see the auth buttons.
        # We send a message here to guide the user.
        bot.send_message(user_id, "❌ محمد عزیز اجازه دسترسی نداده!\n\nلطفاً ابتدا با دستور /start احراز هویت کن.")
        return False
    
    return True # Allow all verified messages to pass

# --- Command Handlers ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handles the /start command and shows the main menu."""
    chat_id = message.chat.id
    
    # Check verification status and show appropriate menu
    if not is_verified(chat_id):
        # Show authentication buttons (simulated)
        markup = types.InlineKeyboardMarkup()
        btn_auth = types.InlineKeyboardButton("🔑 احراز هویت", callback_data="auth_start")
        markup.add(btn_auth)
        bot.send_message(chat_id, "به ربات هوشمند من خوش آمدید. برای شروع، لطفاً احراز هویت کنید.", reply_markup=markup)
        return

    # If verified, show the main menu
    show_main_menu(chat_id)

def show_main_menu(chat_id):
    """Generates and sends the main inline keyboard menu."""
    markup = types.InlineKeyboardMarkup()
    
    # Main Rooms
    btn_tutor = types.InlineKeyboardButton("👨‍🏫 اتاق معلم", callback_data="room_tutor")
    btn_writer = types.InlineKeyboardButton("✍️ اتاق نویسنده", callback_data="room_writer")
    btn_trader = types.InlineKeyboardButton("📈 اتاق تریدر", callback_data="room_trader")
    btn_media = types.InlineKeyboardButton("🎬 اتاق رسانه", callback_data="room_media")
    markup.add(btn_tutor, btn_writer)
    markup.add(btn_trader, btn_media)
    
    # Advanced/Admin Features
    btn_psychology = types.InlineKeyboardButton("🧠 اتاق روانشناسی", callback_data="room_psychology")
    btn_grok = types.InlineKeyboardButton("💡 Grok Mode", callback_data="grok_mode")
    markup.add(btn_psychology, btn_grok)
    
    # Admin Dashboard (Only for Mohammad)
    if is_mohammad(bot.get_chat(chat_id)):
        btn_admin = types.InlineKeyboardButton("⚙️ داشبورد مدیریت", callback_data="admin_dashboard")
        btn_emergency = types.InlineKeyboardButton("🚨 اعلام وضعیت اضطراری", callback_data="emergency_status")
        markup.add(btn_admin, btn_emergency)
        
    # Monetization/Profile
    btn_profile = types.InlineKeyboardButton("👤 پروفایل و اشتراک", callback_data="user_profile")
    btn_market = types.InlineKeyboardButton("💰 بازار اسرار (Stars)", callback_data="secret_market")
    markup.add(btn_profile, btn_market)
    
    bot.send_message(chat_id, "به منوی اصلی خوش آمدید. لطفاً اتاق مورد نظر خود را انتخاب کنید:", reply_markup=markup)

# --- Callback Query Handlers (Navigation and Actions) ---

@bot.callback_query_handler(func=lambda call: call.data.startswith("room_"))
def handle_room_navigation(call):
    room = call.data.split("_")[1]
    chat_id = call.message.chat.id
    
    if room == "tutor":
        msg = "👨‍🏫 به اتاق معلم خوش آمدید. سوالات خود را در مورد ریاضی، فیزیک، برنامه‌نویسی یا زبان بپرسید."
    elif room == "writer":
        msg = "✍️ به اتاق نویسنده خوش آمدید. موضوع مقاله یا پروژه خود را بنویسید."
    elif room == "trader":
        msg = "📈 به اتاق تریدر خوش آمدید. تحلیل تکنیکال، روانشناسی بازار یا آنچین بپرسید."
    elif room == "media":
        msg = "🎬 به اتاق رسانه خوش آمدید. برای تولید تصویر یا ویدیو، درخواست خود را بنویسید."
    elif room == "psychology":
        msg = "🧠 به اتاق روانشناسی خوش آمدید. برای تحلیل شخصیت خود، پیام بفرستید."
    else:
        msg = "اتاق نامشخص."
        
    bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id, f"وارد اتاق {room} شدید.")

@bot.callback_query_handler(func=lambda call: call.data == "admin_dashboard")
def show_admin_dashboard(call):
    if not is_mohammad(call.message):
        bot.answer_callback_query(call.id, "❌ دسترسی غیرمجاز.", show_alert=True)
        return
    
    report = handle_admin_dashboard(call.message)
    
    markup = types.InlineKeyboardMarkup()
    btn_status = types.InlineKeyboardButton("🔄 به‌روزرسانی وضعیت", callback_data="admin_dashboard")
    btn_users = types.InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")
    btn_autonomy = types.InlineKeyboardButton("🚀 گزارش خودکفایی", callback_data="autonomy_mode")
    markup.add(btn_status, btn_users)
    markup.add(btn_autonomy)
    
    bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "autonomy_mode")
def check_autonomy_handler(call):
    if not is_mohammad(call.message): return
    
    report = check_autonomy()
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("🔙 بازگشت به داشبورد", callback_data="admin_dashboard")
    markup.add(btn_back)
    
    bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "secret_market")
def secret_market_handler(call):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("💰 نهنگ‌های بیت‌کوین چی می‌خرن؟ (۵۰ ستاره)", callback_data="buy_whale_data")
    btn2 = types.InlineKeyboardButton("🧠 تحلیل رقیب من (۱۰۰ ستاره)", callback_data="buy_competitor_analysis")
    btn_voice = types.InlineKeyboardButton("🔊 تنظیمات صدا", callback_data="voice_settings")
    markup.add(btn1, btn2)
    markup.add(btn_voice)
    
    bot.edit_message_text("🕵️‍♂️ **به بخش اسرار خوش آمدید.**\nاطلاعاتی که هیچ‌جا پیدا نمی‌کنید را اینجا بخرید:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "auth_start")
def auth_start_handler(call):
    markup = types.InlineKeyboardMarkup()
    btn_google = types.InlineKeyboardButton("🔗 ورود با جیمیل", callback_data="auth_google")
    btn_telegram = types.InlineKeyboardButton("✅ تایید تلگرام", callback_data="auth_telegram")
    markup.add(btn_google, btn_telegram)
    
    bot.edit_message_text("لطفاً روش احراز هویت خود را انتخاب کنید:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("auth_"))
def auth_method_handler(call):
    method = call.data.split("_")[1]
    
    if method == "telegram":
        # Simulate verification success for the admin
        if call.message.chat.id == ADMIN_ID:
            set_user_level(ADMIN_ID, "Owner")
            bot.edit_message_text("✅ احراز هویت موفق! خوش آمدید محمد پادشاه.", call.message.chat.id, call.message.message_id)
            show_main_menu(call.message.chat.id)
        else:
            # For non-admin, they need to be manually verified or pay for a tier
            bot.edit_message_text("❌ احراز هویت ناموفق. لطفاً با ادمین تماس بگیرید یا اشتراک تهیه کنید.", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(f"🔗 در حال ساخت لینک ورود امن برای {method.upper()}...", call.message.chat.id, call.message.message_id)
        # In a real app, this would call start_secure_login from self_improve.py (simulated)
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users_handler(call):
    if not is_mohammad(call.message): return
    
    report = get_user_list()
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("🔙 بازگشت به داشبورد", callback_data="admin_dashboard")
    markup.add(btn_back)
    
    bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "emergency_status")
def emergency_status_handler(call):
    if not is_mohammad(call.message): return
    
    report = system_guardian()
    
    markup = types.InlineKeyboardMarkup()
    btn_secure = types.InlineKeyboardButton("🔒 فعال‌سازی گارد امنیتی", callback_data="activate_guardian")
    btn_back = types.InlineKeyboardButton("🔙 بازگشت به داشبورد", callback_data="admin_dashboard")
    markup.add(btn_secure)
    markup.add(btn_back)
    
    bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "activate_guardian")
def activate_guardian_handler(call):
    if not is_mohammad(call.message): return
    
    bot.answer_callback_query(call.id, "سپر امنیتی فعال شد! 🛡️")
    bot.send_message(call.message.chat.id, "محمد، خیالت راحت! من تمام حرکات مشکوک روی گوشی و هارد ۱ ترابایتی‌ت رو زیر نظر دارم.")
    
    # Return to emergency status menu
    emergency_status_handler(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def secret_market_buy_handler(call):
    item = call.data.split("_")[1]
    chat_id = call.message.chat.id
    
    if item == "whale":
        title = "نهنگ‌های بیت‌کوین چی می‌خرن؟"
        price = 50
    elif item == "competitor":
        title = "تحلیل رقیب من"
        price = 100
    else:
        bot.answer_callback_query(call.id, "❌ آیتم نامعتبر.", show_alert=True)
        return
        
    # In a real app, this would call create_secret_invoice(chat_id, title, price)
    bot.answer_callback_query(call.id, f"در حال ساخت فاکتور پرداخت برای {title}...", show_alert=True)
    bot.send_message(chat_id, f"💰 فاکتور پرداخت برای **{title}** با قیمت **{price} ستاره** آماده شد. (شبیه‌سازی)")

@bot.callback_query_handler(func=lambda call: call.data.startswith("apply_"))
def job_apply_handler(call):
    target = call.data.split("_")[1]
    
    # In a real app, this would send the generated resume and a cover letter
    resume = generate_resume() # Simulated function from self_improve.py
    
    bot.answer_callback_query(call.id, f"رزومه شما برای {target} ارسال شد.", show_alert=True)
    bot.send_message(call.message.chat.id, f"✅ **رزومه ارسال شد!**\n\nبرای {target}، رزومه زیر ارسال گردید:\n{resume}", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "voice_settings")
def voice_settings_handler(call):
    markup = types.InlineKeyboardMarkup()
    btn_male = types.InlineKeyboardButton("👨‍💼 صدای مردانه", callback_data="set_male")
    btn_female = types.InlineKeyboardButton("👩‍💼 صدای زنانه", callback_data="set_female")
    markup.add(btn_male, btn_female)
    
    bot.edit_message_text("محمد جان، دوست داری صدای دستیارت چطوری باشه؟", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_voice_handler(call):
    gender = call.data.split("_")[1]
    result = handle_voice_settings(call.message.chat.id, gender)
    bot.edit_message_text(result, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, result)

# --- General Message Handler (for Gemini/Tool Calls) ---

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handles all non-command messages by passing them to the Gemini agent."""
    chat_id = message.chat.id
    
    # 1. Check for specific admin commands that don't go to Gemini
    if is_mohammad(message):
        if message.text == "/power_up":
            power_up_test(message)
            return
        if message.text == "/find_job":
            job_hunter(message)
            return
        
    # 2. Process message through Gemini
    try:
        # The middleware should have already checked verification, but we check again for safety
        if not is_verified(chat_id):
            bot.send_message(chat_id, "❌ دسترسی محدود شده است. لطفاً با /start احراز هویت کنید.")
            return
            
        # Get response from Super-Agent (Gemini with Tools)
        gemini_text_response = get_gemini_response(message)
        
        # Send to Telegram
        if gemini_text_response:
            bot.send_message(chat_id, gemini_text_response, parse_mode="Markdown")
            
        # Add to Memory
        add_to_memory(chat_id, "user", message.text.strip())
        add_to_memory(chat_id, "bot", gemini_text_response)

    except APIError as e:
        error_message = f"An API error occurred: {e}"
        print(error_message)
        bot.send_message(chat_id, "متأسفانه در حال حاضر به دلیل خطای API نمی‌توانم پاسخ دهم. لطفاً بعداً دوباره تلاش کنید.")
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        bot.send_message(chat_id, "متأسفانه خطای ناشناخته‌ای رخ داد. لطفاً دوباره تلاش کنید.")

# --- Helper Handlers (Admin-specific actions) ---

# --- Helper Handlers (Admin-specific actions) ---

def generate_resume():
    """Simulated function to generate a resume for the bot."""
    return (
        "🤖 **رزومه ادمین هوشمند (Agent Mohammad):**\n"
        "✅ مسلط به مدیریت گروه و حذف اسپم\n"
        "✅ تولید محتوای صوتی و تصویری اختصاصی\n"
        "✅ تحلیلگر تکنیکال بازار کریپتو\n"
        "✅ روانشناس و آدم‌شناس حرفه‌ای\n"
        "💰 حقوق درخواستی: ۵۰۰ ستاره ماهانه"
    )

@bot.message_handler(commands=['power_up'])
def power_up_test(message):
    if not is_mohammad(message):
        return
    
    bot.reply_to(message, "⚡ محمد جان، دارم سیستم رو برای تست نهایی تحت فشار می‌ذارم... صدای فن‌ها رو گوش کن!")
    
    # اجرای تست استرس که قبلاً نوشتیم
    report = hardware_stress_test()
    
    # ساخت یک ویدیوی کوتاه خودکار برای جشن گرفتن قدرت جدید (Simulated)
    # video_path, lesson = make_ai_video(["1000011743.jpg", "1000011732.jpg"], "System_Upgrade_Success")
    
    final_msg = (
        f"{report}\n\n"
        f"🎬 **ویدیو رندر شد:** (شبیه‌سازی)\n"
        f"دستیارت الان خیلی سریع‌تر شده محمد. بریم برای تسخیر بازار! 🚀"
    )
    bot.send_message(message.chat.id, final_msg, parse_mode="Markdown")

@bot.message_handler(commands=['find_job'])
def job_hunter(message):
    if not is_mohammad(message): return
    
    bot.send_message(message.chat.id, "🔍 محمد جان، دارم مثل یک شکارچی دنبال موقعیت‌های شغلی پرسود می‌گردم...")
    
    # جستجو در دیتای جمع‌آوری شده از تلگرام (Simulated)
    jobs = [
        {"target": "@CryptoGroup_Admin", "type": "ادمین چت", "pay": "۲۰۰ ستاره/هفته"},
        {"target": "@Peyment_Support", "type": "پشتیبانی مشتری", "pay": "۵۰ تتر/ماه"}
    ]
    
    for job in jobs:
        markup = types.InlineKeyboardMarkup()
        btn_apply = types.InlineKeyboardButton("📤 ارسال رزومه من", callback_data=f"apply_{job['target']}")
        markup.add(btn_apply)
        
        bot.send_message(message.chat.id, 
                         f"📌 **فرصت شغلی پیدا شد:**\nکانال: {job['target']}\nنوع کار: {job['type']}\nحقوق تخمینی: {job['pay']}", 
                         reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "withdraw_salary")
def handle_salary(call):
    if not is_mohammad(call.message): return
    
    bot.answer_callback_query(call.id, "در حال انتقال درآمدها به حساب پادشاه...")
    bot.send_message(call.message.chat.id, "💵 محمد جان، حقوق این ماه من از ادمینی ۳ کانال، به حساب تتر شما واریز شد!")

# The bot object is exported for use in main.py
