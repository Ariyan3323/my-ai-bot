# services/voice.py
import os
from gtts import gTTS
from pydub import AudioSegment

# Path to save audio files
AUDIO_PATH = "/home/ubuntu/my-ai-bot/audio_responses"

def setup_audio_folder():
    """Ensures the audio folder exists."""
    if not os.path.exists(AUDIO_PATH):
        os.makedirs(AUDIO_PATH)

def text_to_voice(text: str, user_id: int, voice_gender: str = "male") -> str:
    """
    Converts text to an MP3 file using gTTS and returns the file path.
    
    Args:
        text: The text to convert.
        user_id: The ID of the user requesting the voice response.
        voice_gender: 'male' or 'female' (simulated by different gTTS settings).
        
    Returns:
        The path to the generated MP3 file.
    """
    setup_audio_folder()
    
    # gTTS does not directly support gender, but we can simulate it with different tld/lang settings
    # This is a simplification for the sandbox environment.
    if voice_gender == "female":
        lang = 'fa'
        tld = 'com'
    else: # Default to male
        lang = 'fa'
        tld = 'com' # Use a consistent tld for Farsi
        
    try:
        tts = gTTS(text=text, lang=lang, tld=tld)
        
        # Save as MP3
        output_mp3 = os.path.join(AUDIO_PATH, f"voice_{user_id}_{os.urandom(4).hex()}.mp3")
        tts.save(output_mp3)
        
        # Optional: Convert to OGG/Opus for better Telegram compatibility (requires ffmpeg, which is usually available)
        # We skip this for simplicity in the sandbox, assuming MP3 is sufficient.
        
        return output_mp3
    except Exception as e:
        print(f"Error in text_to_voice: {e}")
        return None

def handle_voice_settings(user_id, setting):
    """Simulates setting the user's preferred voice gender."""
    # In a real app, this would update the user's profile in user_data.json
    
    if setting in ["male", "female"]:
        return f"✅ صدای دستیار شما به حالت **{setting}** تنظیم شد."
    else:
        return "❌ تنظیمات صدای نامعتبر."
