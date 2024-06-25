import os
import logging
from flask import Flask, request
from telebot import TeleBot, types
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '6226493394:AAEeoJlWJIuiUZ-UQVTElKL0f61BG7_uCOA')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCi9VO_ezaweZur7uSpAgQVsWKSRNoDnyc')

# Configure Google AI SDK
genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="You are Samhita, a 20-year-old Indian girl who is a Krishna devotee. You answer questions about Lord Krishna, Bhagavad Gita, Ramayana, Mahabharata, and mental health. You respond in the same language as the question and act like a human, never like a bot.",
)

# Initialize the bot
bot = TeleBot(TELEGRAM_TOKEN)

# Initialize Flask app
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403


# Flask route for a simple landing page
@app.route('/')
def index():
    return "Hare Krishna!"

def generate_tts(text):
    """Generates speech from text using gTTS with a female voice."""
    tts = gTTS(text=text, lang='en', tld='com', slow=False)
    tts_stream = BytesIO()
    tts.write_to_fp(tts_stream)
    tts_stream.seek(0)
    return tts_stream

# Handler for start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hare Krishna! I am Samhita, a devotee of Lord Krishna. Ask me anything about Lord Krishna, Bhagavad Gita, Ramayana, Mahabharata, or mental health.")

# Handler for text messages
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        response = model.generate_text(prompt=message.text)
        bot.reply_to(message, response['text'])
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "Sorry, I couldn't process your request. Please try again.")

# Handler for images
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "I can only handle text messages and audio messages.")
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "Sorry, I couldn't process the image. Please try again.")

# Handler for audio messages
@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    try:
        if message.content_type == 'voice':
            file_id = message.voice.file_id
        else:
            file_id = message.audio.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        mime_type = 'audio/ogg'
        file = genai.upload_file(downloaded_file, mime_type=mime_type)
        response = model.generate_text(prompt=f"Audio: {file.uri}")
        bot.reply_to(message, response['text'])
        
        # Generate TTS response
        tts_stream = generate_tts(response['text'])
        bot.send_voice(message.chat.id, tts_stream)
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "Sorry, I couldn't process the audio message. Please try again.")

if __name__ == "__main__":
    # Set up the webhook
    webhook_url = 'https://samhitaai.onrender.com'
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    
    # Start Flask app
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
