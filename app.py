import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from bot import bot, get_gemini_response
from telebot import types as telebot_types

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Get configuration from environment
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# In-memory session storage for web users (for demo purposes)
# In production, use a database like Redis or PostgreSQL
web_sessions = {}

# -----------------------------------------------------------------------
# 1. Web Routes (Serve HTML and Static Files)
# -----------------------------------------------------------------------

@app.route('/', methods=['GET'])
def index():
    """Serve the main web chat interface."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "🤖 Super-Agent is running!",
        "services": {
            "telegram": "connected" if TELEGRAM_TOKEN else "not configured",
            "gemini": "connected" if GEMINI_API_KEY else "not configured"
        }
    }), 200

# -----------------------------------------------------------------------
# 2. API Endpoints for Web Chat
# -----------------------------------------------------------------------

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    API endpoint for web chat interface.
    Accepts a message and returns a response from the Super-Agent.
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({
                "success": False,
                "error": "پیام خالی است."
            }), 400

        # Create a mock Telegram message object for compatibility with get_gemini_response
        mock_message = MockMessage(user_message)

        # Get response from the Super-Agent (Gemini with Tools)
        response_text = get_gemini_response(mock_message)

        return jsonify({
            "success": True,
            "reply": response_text if response_text else "متأسفانه نتوانستم پاسخی تولید کنم."
        }), 200

    except Exception as e:
        print(f"Error in /api/chat: {e}")
        return jsonify({
            "success": False,
            "error": f"خطای سرور: {str(e)}"
        }), 500

@app.route('/api/info', methods=['GET'])
def api_info():
    """Get information about the Super-Agent."""
    return jsonify({
        "name": "Super-Agent",
        "version": "1.0.0",
        "description": "دستیار هوشمند محمد - معلم، نویسنده، تریدر و محافظ شخصی",
        "features": [
            "آموزش تخصصی (ریاضی، فیزیک، برنامه‌نویسی)",
            "نویسندگی حرفه‌ای",
            "مشاوره حقوقی",
            "تحلیل ترید",
            "تولید رسانه",
            "تحلیل شخصیت",
            "مانیتورینگ سخت‌افزار",
            "شکارچی سود"
        ],
        "contact": "https://t.me/my_ai_bot"
    }), 200

# -----------------------------------------------------------------------
# 3. Telegram Webhook Routes (for Telegram integration)
# -----------------------------------------------------------------------

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming Telegram updates via POST request."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot_types.Update.de_json(json.loads(json_string))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Invalid Content Type', 400

@app.route('/setwebhook', methods=['GET'])
def set_webhook_route():
    """Sets the Telegram webhook URL."""
    if WEBHOOK_URL:
        try:
            bot.set_webhook(url=WEBHOOK_URL + "/webhook")
            return jsonify({
                "status": "success",
                "message": "Webhook set successfully!",
                "url": WEBHOOK_URL + "/webhook"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Failed to set webhook: {str(e)}"
            }), 500
    return jsonify({
        "status": "error",
        "message": "WEBHOOK_URL environment variable not set."
    }), 400

# -----------------------------------------------------------------------
# 4. Helper Classes
# -----------------------------------------------------------------------

class MockMessage:
    """
    Mock Telegram message object for compatibility with get_gemini_response.
    This allows the web interface to use the same response logic as Telegram.
    """
    def __init__(self, text):
        self.text = text
        self.from_user = MockUser()
        self.chat = MockChat()

class MockUser:
    """Mock Telegram user object."""
    def __init__(self):
        self.id = 0  # Web users have ID 0 (not authenticated as admin)
        self.first_name = "Web User"
        self.username = "web_user"

class MockChat:
    """Mock Telegram chat object."""
    def __init__(self):
        self.id = 0

# -----------------------------------------------------------------------
# 5. Error Handlers
# -----------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "message": "صفحه یافت نشد."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "status": "error",
        "message": "خطای داخلی سرور."
    }), 500

# -----------------------------------------------------------------------
# 6. Application Entry Point
# -----------------------------------------------------------------------

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run Flask app
    app.run(host="0.0.0.0", port=port, debug=False)
