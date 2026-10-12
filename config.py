import os
import re
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (BotFather'dan olingan)
raw_token = os.getenv("BOT_TOKEN", "").strip()
token_match = re.search(r'(\d+:[A-Za-z0-9_-]+)', raw_token)
BOT_TOKEN = token_match.group(1) if token_match else raw_token.strip('"\'')

# AI Sozlamalari (Google Gemini yoki OpenAI)
raw_gemini = os.getenv("GEMINI_API_KEY", "").strip()
gemini_match = re.search(r'(AQ\.[A-Za-z0-9_-]+|AIza[A-Za-z0-9_-]+)', raw_gemini)
GEMINI_API_KEY = gemini_match.group(1) if gemini_match else raw_gemini.strip('"\'')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().strip('"\'')

# Ma'lumotlar bazasi fayli
DB_PATH = os.getenv("DB_PATH", "hisobchi.db").strip().strip('"\'')
