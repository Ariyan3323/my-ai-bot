# services/memory.py
import json
import os
from datetime import datetime

# Path to the local storage on the 1TB hard drive (simulated for sandbox)
MEMORY_FILE = "/home/ubuntu/my-ai-bot/user_memory.json"
MAX_MESSAGES = 10

def load_memory():
    """Loads user memory from the local JSON file."""
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(memory):
    """Saves user memory to the local JSON file."""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving memory: {e}")

def add_to_memory(user_id, role, text):
    """Adds a message to the user's conversation history."""
    memory = load_memory()
    user_id_str = str(user_id)
    
    if user_id_str not in memory:
        memory[user_id_str] = {"history": [], "personality": "نامشخص"}
        
    # Add new message
    new_entry = {
        "role": role,
        "text": text,
        "timestamp": datetime.now().isoformat()
    }
    memory[user_id_str]["history"].append(new_entry)
    
    # Keep only the last MAX_MESSAGES
    memory[user_id_str]["history"] = memory[user_id_str]["history"][-MAX_MESSAGES:]
    
    save_memory(memory)

def get_history(user_id):
    """Retrieves the conversation history for a user."""
    memory = load_memory()
    user_id_str = str(user_id)
    
    if user_id_str in memory:
        # Format history for use by the LLM (e.g., Gemini)
        formatted_history = []
        for entry in memory[user_id_str]["history"]:
            formatted_history.append(f"[{entry['role']}]: {entry['text']}")
        return "\n".join(formatted_history)
    
    return ""

def get_personality(user_id):
    """Retrieves the user's analyzed personality."""
    memory = load_memory()
    user_id_str = str(user_id)
    
    return memory.get(user_id_str, {}).get("personality", "نامشخص")

def update_personality(user_id, new_personality):
    """Updates the user's analyzed personality."""
    memory = load_memory()
    user_id_str = str(user_id)
    
    if user_id_str not in memory:
        memory[user_id_str] = {"history": [], "personality": "نامشخص"}
        
    memory[user_id_str]["personality"] = new_personality
    save_memory(memory)
    
    return f"✅ تحلیل شخصیت کاربر {user_id} به '{new_personality}' به‌روزرسانی شد."

def handle_personality_analysis(user_id):
    """Simulates a detailed personality analysis based on history."""
    history = get_history(user_id)
    
    if not history:
        return "❌ سابقه مکالمه کافی برای تحلیل شخصیت وجود ندارد."
    
    # In a real application, this would call Gemini with the history to perform analysis.
    # For now, we simulate a result based on the user's ID.
    
    if str(user_id) == "33230000":
        personality = "پادشاه، کارآفرین، و علاقه‌مند به سخت‌افزار و ترید"
    else:
        personality = "کاربر عادی، محتاط، و علاقه‌مند به آموزش"
        
    update_personality(user_id, personality)
    
    return (
        f"🧠 **گزارش تحلیل شخصیت کاربر {user_id}:**\n\n"
        f"تیپ شخصیتی: **{personality}**\n"
        f"بر اساس {len(history.splitlines())} پیام آخر، این کاربر:\n"
        f"🔹 به دنبال سودآوری سریع است.\n"
        f"🔹 به امنیت و حریم خصوصی اهمیت می‌دهد.\n"
        f"🔹 از لحن محترمانه استفاده می‌کند."
    )
