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

# --- OpenAI Client & Multi-Engine Integration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI client initialized successfully.")
    except Exception as oe:
        print(f"OpenAI initialization error: {oe}")

def call_openai_fallback(prompt, image_bytes=None):
    """Calls OpenAI GPT-4o as a multi-model fallback or supplementary engine."""
    if not openai_client:
        return None
    try:
        if image_bytes:
            b64_img = base64.b64encode(image_bytes).decode('utf-8')
            resp = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }],
                max_tokens=1000
            )
            return resp.choices[0].message.content
        else:
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            return resp.choices[0].message.content
    except Exception as err:
        print(f"OpenAI fallback error: {err}")
        return None


# Telegram and Gemini API Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("Error: TELEGRAM_TOKEN or GEMINI_API_KEY not found in environment variables.")

bot = TeleBot(TELEGRAM_TOKEN)
# Gemini API Keys with Automatic Failover / Rotation
raw_keys = os.getenv("GEMINI_API_KEYS", "")
keys_list = [k.strip() for k in raw_keys.split(",") if k.strip()]
single_key = os.getenv("GEMINI_API_KEY")
if single_key and single_key not in keys_list:
    keys_list.insert(0, single_key)

# Fallback for extra indexed keys like GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
for i in range(1, 10):
    k = os.getenv(f"GEMINI_API_KEY_{i}")
    if k and k.strip() and k.strip() not in keys_list:
        keys_list.append(k.strip())

if not keys_list:
    print("Warning: No GEMINI_API_KEY found in environment variables.")

current_key_index = 0

try:
    client = genai.Client(api_key=keys_list[0]) if keys_list else None
except Exception:
    client = None

def get_current_gemini_client():
    global current_key_index, keys_list
    if not keys_list:
        raise ValueError("هیچ کلید API جمینای تنظیم نشده است!")
    return genai.Client(api_key=keys_list[current_key_index])

def rotate_to_next_key():
    global current_key_index, keys_list
    if len(keys_list) > 1:
        current_key_index = (current_key_index + 1) % len(keys_list)
        print(f"Switched to Gemini API key index: {current_key_index} of {len(keys_list)}")
        return True
    return False

def call_gemini_with_fallback(func, *args, **kwargs):
    global keys_list
    attempts = max(1, len(keys_list))
    last_error = None
    for _ in range(attempts):
        try:
            client = get_current_gemini_client()
            return func(client, *args, **kwargs)
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            print(f"Gemini call error on key {current_key_index}: {e}")
            if "429" in err_str or "quota" in err_str or "exhausted" in err_str or "key" in err_str or "not found" in err_str or "permission" in err_str:
                if not rotate_to_next_key():
                    break
            else:
                break
    raise last_error

FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-flash-latest", "gemini-2.0-flash-exp", "gemini-2.5-flash"]
model_name = FALLBACK_MODELS[0]

def generate_with_model_fallback(c=None, contents=None, config=None):
    """Tries available models and rotates keys if Google servers return errors."""
    global client, current_key_index, keys_list
    attempts = max(1, len(keys_list)) if keys_list else 1
    last_err = None
    for _ in range(attempts):
        try:
            active_client = get_current_gemini_client() if keys_list else (c or client)
        except Exception:
            active_client = c or client

        if active_client:
            for m in FALLBACK_MODELS:
                try:
                    res = active_client.models.generate_content(
                        model=m,
                        contents=contents,
                        config=config
                    )
                    return res
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    print(f"Model {m} failed ({e}), trying next model...")
                    if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                        break
                    continue
        if keys_list and len(keys_list) > 1:
            if not rotate_to_next_key():
                break
        else:
            break

    # If all Gemini models failed and OpenAI is available, fallback to OpenAI
    if openai_client and isinstance(contents, str):
        print("Falling back to OpenAI...")
        openai_resp = call_openai_fallback(contents)
        if openai_resp:
            class DummyResp:
                text = openai_resp
                function_calls = None
            return DummyResp()

    if last_err:
        raise last_err
    raise RuntimeError("No AI model available.")


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
    response = generate_with_model_fallback(client,

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
        response = generate_with_model_fallback(client,

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
        if call.message.chat.id in (ADMIN_ID, 6643590715):
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



# --- Multimodal & Generation Handlers ---

def clean_text_for_tts(t: str) -> str:
    if not t:
        return ""
    import re
    t = re.sub(r'http\S+', '', t)
    for c in ['*', '_', '`', '#', '~', '>', '•', '-']:
        t = t.replace(c, '')
    if len(t) > 400:
        t = t[:380] + '...'
    return t.strip()

def check_image_intent(msg_text: str):
    if not msg_text:
        return None
    import re
    t = msg_text.strip()
    kws = ["بکش", "نقاشی", "طراحی", "تصویر", "عکس", "draw", "paint", "image", "photo", "pic"]
    # Skip if asking about an already sent photo
    if any(neg in t for neg in ["این عکس", "تحلیل عکس", "این تصویر", "این چیه"]):
        return None
    for k in kws:
        if k in t.lower():
            p = t
            for w in ["لطفا", "لطفاً", "برام", "واسم", "میشه", "یه", "یک", "بکشی", "بکش", "نقاشی کن", "نقاشی", "طراحی کن", "طراحی", "تصویر بساز", "تصویر یک", "عکس بساز", "عکس یک", "عکس", "بده", "کن"]:
                p = re.sub(r'\b' + re.escape(w) + r'\b', '', p)
            p = p.strip()
            return p if len(p) > 1 else t
    return None

def free_online_search(query: str) -> str:
    """Fetches free online knowledge from DuckDuckGo when keys fail or for live info."""
    try:
        import urllib.request, urllib.parse, json
        q = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            ans = data.get('AbstractText') or data.get('Answer')
            if ans:
                return ans
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
    return None


import urllib.parse

@bot.message_handler(commands=['generate', 'draw', 'image'])
def handle_generate_image_command(message):
    """Generates an image based on user prompt using AI."""
    chat_id = message.chat.id
    prompt = message.text.partition(' ')[2].strip()
    if not prompt:
        bot.reply_to(message, "🎨 لطفاً موضوع یا توصیف عکسی که می‌خوای رو بعد از دستور بنویس. مثال: /draw یک فضانورد در فضا", parse_mode="Markdown")
        return

    status_msg = bot.reply_to(message, f"🎨 در حال طراحی و خلق تصویر برای: _{prompt}_...", parse_mode="Markdown")
    try:
        # Prompt translation/enhancement or direct URL via Pollinations AI
        import urllib.request
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        img_req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(img_req, timeout=35) as img_resp:
            img_bytes = img_resp.read()
        bot.send_photo(chat_id, img_bytes, caption=f"🖼️ تصویر شما برای: *{prompt}*", parse_mode="Markdown")
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except Exception:
            pass
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در ساخت تصویر: {e}")

@bot.message_handler(content_types=['photo'])
def handle_incoming_photo(message):
    chat_id = message.chat.id
    if not is_verified(chat_id):
        bot.send_message(chat_id, "⛔ دسترسی محدود است. لطفاً با /start احراز هویت کنید.")
        return

    status_msg = bot.reply_to(message, "👁️ در حال نگاه کردن به عکس و تحلیل آن با هوش مصنوعی...")
    try:
        photo_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(photo_info.file_path)

        user_caption = message.caption.strip() if message.caption else "این تصویر را با جزئیات کامل به زبان فارسی تحلیل و بررسی کن."
        reply_text = None

        # 1. Try Gemini
        gemini_error = None
        try:
            image_part = gemini_types.Part.from_bytes(data=downloaded_file, mime_type="image/jpeg")
            resp = generate_with_model_fallback(contents=[image_part, user_caption])
            if resp and hasattr(resp, 'text') and resp.text:
                reply_text = resp.text
        except Exception as ge:
            gemini_error = ge
            print(f"Gemini photo error: {ge}")

        # 2. OpenAI GPT-4o Vision Fallback
        if not reply_text and openai_client:
            try:
                import base64
                b64 = base64.b64encode(downloaded_file).decode('utf-8')
                v_resp = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_caption},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                            ]
                        }
                    ],
                    max_tokens=600
                )
                reply_text = v_resp.choices[0].message.content
            except Exception as oe:
                print(f"OpenAI photo error: {oe}")

        if not reply_text:
            if gemini_error:
                reply_text = f"⚠️ خطا در تحلیل تصویر با جمینای: {gemini_error}"
            else:
                reply_text = "متأسفانه در تحلیل تصویر خطایی رخ داد. لطفاً کیفیت عکس را بررسی یا مجدداً ارسال کنید."

        bot.reply_to(message, reply_text)
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except Exception:
            pass
    except Exception as e:
        print(f"Photo error: {e}")
        bot.reply_to(message, f"❌ خطا در تحلیل تصویر: {e}")

@bot.message_handler(content_types=['voice', 'audio'])
def handle_incoming_voice(message):
    chat_id = message.chat.id
    if not is_verified(chat_id):
        bot.send_message(chat_id, "⛔ دسترسی محدود است. لطفاً با /start احراز هویت کنید.")
        return

    status_msg = bot.reply_to(message, "🎙️ در حال گوش دادن و آماده‌سازی پاسخ صوتی...")
    try:
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file_info = bot.get_file(file_id)
        downloaded_audio = bot.download_file(file_info.file_path)

        audio_part = gemini_types.Part.from_bytes(data=downloaded_audio, mime_type="audio/ogg")
        voice_prompt = "این فایل صوتی را گوش کن و به زبان فارسی پاسخی کامل، گرم و صمیمی بده."

        response = generate_with_model_fallback(client, contents=[audio_part, voice_prompt])
        reply_text = response.text if (response and hasattr(response, 'text') and response.text) else "صدا دریافت شد."

        bot.reply_to(message, reply_text)
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except Exception:
            pass

        # Send Voice response back to user
        try:
            spoken = clean_text_for_tts(reply_text)
            if spoken:
                vp = text_to_voice(spoken, chat_id)
                if vp and os.path.exists(vp):
                    with open(vp, 'rb') as vf:
                        bot.send_voice(chat_id, vf, caption="🎙️ پاسخ صوتی شما")
                    try:
                        os.remove(vp)
                    except Exception:
                        pass
        except Exception as ve:
            print(f"Voice generation error: {ve}")
    except Exception as e:
        print(f"Voice error: {e}")
        bot.reply_to(message, f"❌ خطا در پردازش صدا: {e}")

# --- General Message Handler ---

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    if is_mohammad(message):
        if message.text == "/power_up":
            power_up_test(message)
            return
        if message.text == "/find_job":
            job_hunter(message)
            return

    if not is_verified(chat_id):
        bot.send_message(chat_id, "❌ دسترسی محدود شده است. لطفاً با /start احراز هویت کنید.")
        return

    text = message.text or ""

    # 1. Natural Image Generation Intent
    img_prompt = check_image_intent(text)
    if img_prompt and len(img_prompt) > 2:
        status_msg = bot.reply_to(message, f"🎨 در حال طراحی و خلق تصویر برای: *{img_prompt}*...", parse_mode="Markdown")
        try:
            import urllib.parse, urllib.request
            encoded = urllib.parse.quote(img_prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
            img_req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req, timeout=35) as img_resp:
                img_bytes = img_resp.read()
            bot.send_photo(chat_id, img_bytes, caption=f"🖼️ بفرمایید، تصویر شما برای: *{img_prompt}*", parse_mode="Markdown")
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except Exception:
                pass
            return
        except Exception as e:
            bot.send_message(chat_id, f"❌ خطا در ساخت تصویر: {e}")
            return

    # 2. Main response (Gemini / OpenAI / Online search fallback)
    try:
        gemini_text_response = None
        try:
            gemini_text_response = get_gemini_response(message)
        except Exception as api_err:
            print(f"API error, trying online search fallback: {api_err}")
            online_info = free_online_search(text)
            if online_info:
                gemini_text_response = f"🌐 اطلاعات آنلاین:\n{online_info}"

        if gemini_text_response:
            bot.send_message(chat_id, gemini_text_response)

            # Auto-detect if Gemini generated an image prompt instead of an image
            if "Prompt:" in gemini_text_response or "پرامپت" in gemini_text_response:
                try:
                    import re, urllib.parse, urllib.request
                    m = re.search(r'Prompt:\*?\*?\s*(?:>)?\s*\*?(.*?)\*?(?:\n\n|$)', gemini_text_response, re.DOTALL | re.IGNORECASE)
                    extracted_prompt = m.group(1).strip().strip('*').strip() if m else None
                    if extracted_prompt and len(extracted_prompt) > 5:
                        bot.send_chat_action(chat_id, 'upload_photo')
                        enc = urllib.parse.quote(extracted_prompt[:300])
                        img_url = f"https://image.pollinations.ai/prompt/{enc}?width=1024&height=1024&nologo=true"
                        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=30) as r:
                            img_b = r.read()
                        bot.send_photo(chat_id, img_b, caption="🖼️ تصویر طراحی شده:")
                except Exception as pe:
                    print(f"Auto-draw prompt error: {pe}")

            # If user explicitly asked for voice
            if any(w in text.lower() for w in ["ویس", "صوتی", "بخون", "voice", "audio"]):
                try:
                    spoken = clean_text_for_tts(gemini_text_response)
                    vp = text_to_voice(spoken, chat_id)
                    if vp and os.path.exists(vp):
                        with open(vp, 'rb') as vf:
                            try:
                                bot.send_voice(chat_id, vf)
                            except Exception:
                                vf.seek(0)
                                bot.send_audio(chat_id, vf, title="پاسخ صوتی")
                        try:
                            os.remove(vp)
                        except Exception:
                            pass
                except Exception as ve:
                    print(f"Voice reply error: {ve}")
        else:
            bot.reply_to(message, "⚠️ در حال حاضر به دلیل محدودیت موقت سرورهای هوش مصنوعی امکان دریافت پاسخ نبود. لطفاً لحظاتی بعد مجدداً تلاش کنید.")

    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

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


# --- Group & Channel Evolution Handlers ---

@bot.my_chat_member_handler()
def handle_bot_membership_change(update):
    """Automatically introduces and configures itself when added to a group or channel."""
    chat = update.chat
    new_status = update.new_chat_member.status
    if new_status in ['member', 'administrator']:
        intro_text = (
            f"🌟 **سلام به اعضای محترم {chat.title or 'گروه'}!**\n\n"
            "من دستیار هوشمند، تحلیلگر بازار و ایجنت پیشرفته محمد هستم.\n"
            "📌 **قابلیت‌ها:**\n"
            "🔹 تحلیل عکس‌ها و تصاویر با دید بصری هوش مصنوعی\n"
            "🔹 شنیدن و پاسخ به پیام‌های صوتی (ویس)\n"
            "🔹 طراحی و ساخت تصویر با دستور /draw یا /image\n"
            "🔹 پاسخ به سؤالات علمی، نگارش، حقوقی و ترید\n\n"
            "آماده خدمت‌رسانی و یادگیری در این فضا هستم! 🚀"
        )
        try:
            bot.send_message(chat.id, intro_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to send group intro: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    """Greets new members entering the group."""
    for new_member in message.new_chat_members:
        if new_member.id != bot.get_me().id:
            first_name = new_member.first_name or "دوست عزیز"
            bot.reply_to(message, f"خوش آمدید {first_name}! 🌹 اگر سؤالی داشتید، من دستیار هوش مصنوعی گروه در خدمتم.")

@bot.message_handler(commands=['gpt', 'openai'])
def handle_gpt_command(message):
    """Direct query to OpenAI GPT-4o."""
    prompt = message.text.partition(' ')[2].strip()
    if not prompt:
        bot.reply_to(message, "لطفاً سؤال یا درخواست خود را بعد از دستور /gpt بنویسید.")
        return
    if not openai_client:
        bot.reply_to(message, "⚠️ کلید OPENAI_API_KEY در فایل .env تنظیم نشده است.")
        return
    status = bot.reply_to(message, "🧠 در حال پرسش از OpenAI GPT-4o...")
    ans = call_openai_fallback(prompt)
    if ans:
        bot.reply_to(message, ans)
    else:
        bot.reply_to(message, "خطا در دریافت پاسخ از OpenAI.")
    try:
        bot.delete_message(message.chat.id, status.message_id)
    except Exception:
        pass
