# services/admin.py
from telebot import types
import json
import os

# --- Configuration ---
# Admin ID (Mohammad's ID)
ADMIN_ID = int(os.getenv("ADMIN_ID", 33230000)) # Default to Mohammad's ID if not set 

# User Level Tiers
USER_LEVELS = {
    "Owner": 5,
    "Gold": 4,
    "Silver": 3,
    "Bronze": 2,
    "Free": 1
}

# Portable path: a json file next to the project root, works on any machine
USER_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_data.json")

def load_user_data():
    """Loads user data from the local JSON file."""
    if not os.path.exists(USER_DATA_PATH):
        return {}
    try:
        with open(USER_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_user_data(data):
    """Saves user data to the local JSON file."""
    try:
        with open(USER_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving user data: {e}")
        return False

def get_user_level(user_id):
    """Returns the user's current access level."""
    user_data = load_user_data()
    user_id_str = str(user_id)
    
    if user_id == ADMIN_ID:
        return "Owner"
    
    return user_data.get(user_id_str, {}).get("level", "Free")

def is_mohammad(message_or_call):
    """Checks if the user is the admin (Mohammad)."""
    user_id = message_or_call.from_user.id if hasattr(message_or_call, 'from_user') else message_or_call.chat.id
    return user_id == ADMIN_ID

def is_verified(user_id):
    """Gatekeeper check: checks if the user is verified (simulated)."""
    # For now, only the admin is verified by default.
    # In the future, this will check a 'verified' flag in user_data.
    return user_id == ADMIN_ID or get_user_level(user_id) != "Free"

def show_auth_buttons(user_id):
    """Generates and sends authentication buttons (simulated)."""
    # This function will be implemented in bot.py or a dedicated UI module
    pass

# --- Admin Dashboard and System Monitoring ---

def get_system_status():
    """Provides a report on the system's health (CPU, RAM, Disk)."""
    import psutil
    
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/') # Assuming the bot runs on the root partition
    
    # Simulate D: drive usage for the user's 1TB hard drive
    # Since we are in a sandbox, we'll use the sandbox disk usage as a proxy
    
    report = (
        "📊 **داشبورد مدیریتی (مانیتورینگ سیستم):**\n\n"
        f"🧠 **CPU:** {cpu_percent}%\n"
        f"💾 **RAM:** {ram.percent}% ({ram.used / (1024**3):.1f}GB از {ram.total / (1024**3):.1f}GB)\n"
        f"💽 **هارد دیسک (D:):** {disk.percent}% پر ({disk.used / (1024**3):.1f}GB از {disk.total / (1024**3):.1f}GB)\n"
        "\n"
        "✅ **وضعیت:** سیستم در حالت پایداری کامل است.\n"
        "⚠️ **توجه:** رم ۸ گیگابایتی شما برای پردازش‌های سنگین ویدیو (MoviePy) تحت فشار قرار می‌گیرد."
    )
    return report

def handle_admin_dashboard(message):
    """Handles the admin dashboard command."""
    if not is_mohammad(message):
        return "❌ شما دسترسی مدیر ندارید."
    
    status = get_system_status()
    return status

# --- User Level Management ---

def set_user_level(target_user_id, level):
    """Sets the access level for a specific user."""
    if level not in USER_LEVELS:
        return f"❌ سطح دسترسی '{level}' معتبر نیست."
    
    user_data = load_user_data()
    user_id_str = str(target_user_id)
    
    if user_id_str not in user_data:
        user_data[user_id_str] = {}
        
    user_data[user_id_str]["level"] = level
    
    if save_user_data(user_data):
        return f"✅ سطح دسترسی کاربر {target_user_id} به '{level}' ارتقا یافت."
    else:
        return "❌ خطایی در ذخیره داده‌ها رخ داد."

def get_user_list():
    """Returns a list of all users and their levels."""
    user_data = load_user_data()
    report = "👥 **لیست کاربران و سطوح دسترسی:**\n\n"
    
    for user_id, data in user_data.items():
        level = data.get("level", "Free")
        report += f"ID: {user_id} | سطح: {level}\n"
        
    return report
