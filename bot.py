import os
import json
from dotenv import load_dotenv
from telebot import TeleBot
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Import Service Modules
from services.ethics import is_ethical_request, get_ethics_rejection_message
from services.trader import handle_trader_request
from services.legal import handle_legal_request
from services.tutor import handle_tutor_request
from services.writer import handle_writing_request
from services.premium import check_access_level, get_premium_features
from services.image_generator import handle_image_request

# ----------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------
load_dotenv()

# Telegram and Gemini API Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    # In a real deployment, we would raise an error, but for the sandbox, we print and exit
    print("Error: TELEGRAM_TOKEN or GEMINI_API_KEY not found in environment variables.")
    # For deployment, we assume these are set
    # exit() 

bot = TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)
model_name = "gemini-2.5-flash"

# Map function names to actual functions for execution
tool_functions = {
    "handle_trader_request": handle_trader_request,
    "handle_legal_request": handle_legal_request,
    "handle_tutor_request": handle_tutor_request,
    "handle_writing_request": handle_writing_request,
    "handle_image_request": handle_image_request,
    "check_access_level": check_access_level,
    "get_premium_features": get_premium_features,
}

# ----------------------------------------------------------------------
# 2. Core Agent Logic (Function Calling)
# ----------------------------------------------------------------------

def get_gemini_response(prompt):
    """Sends prompt to Gemini and handles function calls."""
    
    # All service functions are passed as tools to the model
    tools = [
        handle_trader_request,
        handle_legal_request,
        handle_tutor_request,
        handle_writing_request,
        handle_image_request,
        check_access_level,
        get_premium_features,
    ]
    
    # System Instruction to guide the model's behavior
    system_instruction = (
        "You are a Super-Agent for the Iranian market, specialized in trading, "
        "Iranian law, academic tutoring, and professional writing. "
        "Your primary language is Farsi (Persian). "
        "Use the provided tools to answer specific user requests. "
        "If a tool is available, you MUST use it. If no tool is relevant, "
        "answer the user's question directly in Farsi."
    )

    # Use generate_content for a single turn with tools
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=tools,
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
                # In a real app, user_id would be passed here. For this example, we use a placeholder.
                if function_name == "check_access_level":
                    args["user_id"] = 12345 
                
                # Execute the function with arguments
                function_result = local_function(**args)
                
                # Prepare the tool response for the model
                tool_responses.append(
                    types.Part.from_function_response(
                        name=function_name,
                        response={"result": function_result}
                    )
                )
            else:
                # Handle unknown function call
                tool_responses.append(
                    types.Part.from_function_response(
                        name=function_name,
                        response={"error": f"Unknown function: {function_name}"}
                    )
                )

        # Send the function results back to the model
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, *tool_responses], # Send original prompt + tool results
            config=types.GenerateContentConfig(
                tools=tools,
                system_instruction=system_instruction
            )
        )
        
    return response.text

# ----------------------------------------------------------------------
# 3. Telegram Message Handler
# ----------------------------------------------------------------------

def process_message(message_json):
    """Processes incoming Telegram message from Webhook."""
    try:
        update = types.Update.from_json(message_json)
        message = update.message
        
        if not message or not message.text:
            return # Ignore non-text messages

        chat_id = message.chat.id
        text = message.text.strip()
        
        # --- 1. Ethics Filter (First Line of Defense) ---
        if not is_ethical_request(text):
            rejection_message = get_ethics_rejection_message(lang="fa") # Assuming default Farsi
            bot.send_message(chat_id, rejection_message, parse_mode="Markdown")
            return

        # --- 2. Get Response from Super-Agent (Gemini with Tools) ---
        gemini_text_response = get_gemini_response(text)
        
        # --- 3. Send to Telegram ---
        if gemini_text_response:
            bot.send_message(chat_id, gemini_text_response, parse_mode="Markdown")

    except APIError as e:
        error_message = f"An API error occurred: {e}"
        print(error_message)
        bot.send_message(chat_id, "متأسفانه در حال حاضر به دلیل خطای API نمی‌توانم پاسخ دهم. لطفاً بعداً دوباره تلاش کنید.")
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        bot.send_message(chat_id, "متأسفانه خطای ناشناخته‌ای رخ داد. لطفاً دوباره تلاش کنید.")

# The bot object is exported for use in main.py
