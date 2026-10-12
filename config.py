import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (BotFather'dan olinadi)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# AI Sozlamalari (Google Gemini yoki OpenAI)
# Gemini bepul kalit olish: https://aistudio.google.com/
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Ma'lumotlar bazasi fayli
DB_PATH = os.getenv("DB_PATH", "hisobchi.db")
