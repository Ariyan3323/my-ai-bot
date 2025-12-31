import os
from flask import Flask, request, jsonify
from bot import bot, process_message

# ----------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------
app = Flask(__name__)

# Get Webhook URL from environment variables (e.g., set by Render)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") 

# ----------------------------------------------------------------------
# 2. Webhook Routes
# ----------------------------------------------------------------------

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming Telegram updates via POST request."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        
        # Process the message using the logic from bot.py
        process_message(json_string)
        
        return 'OK', 200
    return 'Invalid Content Type', 400

@app.route('/setwebhook', methods=['GET'])
def set_webhook_route():
    """Sets the Telegram webhook URL."""
    if WEBHOOK_URL:
        # Telegram API call to set the webhook
        bot.set_webhook(url=WEBHOOK_URL + "/webhook")
        return jsonify({"status": "Webhook set successfully!", "url": WEBHOOK_URL + "/webhook"})
    return jsonify({"error": "WEBHOOK_URL environment variable not set."})

@app.route('/', methods=['GET'])
def health():
    """Health check endpoint."""
    return '🤖 Super-Agent is running!'

# ----------------------------------------------------------------------
# 3. Local Run (for testing, not used in production deployment)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # This block is typically for local development
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
