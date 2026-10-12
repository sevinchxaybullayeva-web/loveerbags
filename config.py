import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (BotFather'dan olingan)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip().strip('"').strip("'")

# AI Sozlamalari (Google Gemini yoki OpenAI)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")

# Ma'lumotlar bazasi fayli
DB_PATH = os.getenv("DB_PATH", "hisobchi.db")
