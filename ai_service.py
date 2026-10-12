import json
import re
import aiohttp
from typing import Dict, Any, Optional
from config import GEMINI_API_KEY, OPENAI_API_KEY

SYSTEM_PROMPT = """Siz do'kon va savdo hisobchisi bo'lgan Telegram bot uchun sun'iy intellekt (AI) yordamchisisiz.
Vazifangiz foydalanuvchining o'zbek tilidagi erkin matnli yoki ovozli xabarlarini tahlil qilish va ma'lumotlarni aniq ajratib olish.

Quyidagi amallardan birini aniqlang va FAQAT toza JSON formatida javob qaytaring:

1. TOVAR QO'SHISH / YANGILASH:
Foydalanuvchi tovar (mahsulot) haqida yozganda:
Maxsus raqami (kod/artikul), tovar nomi, soni, tan narxi va sotuv narxini aniqlang.
{
  "action": "add_product",
  "data": {
    "code": "tovar maxsus kodi yoki artikul (masalan: 101, A-45, 9942)",
    "name": "tovar nomi (masalan: Ayollar sumkasi, Krossovka)",
    "quantity": 10.0,
    "cost_price": 50000.0,
    "sale_price": 75000.0
  },
  "message": "Foydalanuvchi uchun xushmuomala xabar"
}

2. QARZ YOZISH (NASIYA):
Foydalanuvchi kimningdir qarzi haqida yozganda:
Qarzdor ismi, summa va izohni aniqlang.
{
  "action": "add_debt",
  "data": {
    "debtor_name": "Qarzdor ismi (masalan: Alisher aka, Sardor)",
    "amount": 250000.0,
    "description": "qarz sababi yoki muddati"
  },
  "message": "Foydalanuvchi uchun xushmuomala xabar"
}

3. STATISTIKA / HISOBOT SO'ROVI:
Tovarlar yoki qarzlar haqida so'raganda:
{
  "action": "get_stats",
  "data": {
    "target": "products"
  },
  "message": "Hisobot"
}

4. ODDIY SUHBAT / SALOMLASHISH / SAVOL:
{
  "action": "chat",
  "data": {},
  "message": "Foydalanuvchiga samimiy o'zbek tilidagi javob"
}

DIQQAT:
- Har qanday narx yoki qarz summasida "ming" bo'lsa * 1000, "mln" bo'lsa * 1 000 000 deb hisoblang.
- Faqat JSON qaytaring, ortiqcha hech narsa yozmang!
"""

async def analyze_with_gemini(text: str) -> Optional[Dict[str, Any]]:
    """Google Gemini API orqali matnni tahlil qilish"""
    if not GEMINI_API_KEY:
        return None

    # Google Gemini API endpoint (gemini-flash-latest yoki gemini-2.5-flash)
    models_to_try = ["gemini-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT},
                    {"text": f"Foydalanuvchi xabari: {text}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2
        }
    }

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=12) as response:
                    if response.status == 200:
                        result = await response.json()
                        candidates = result.get("candidates", [])
                        if candidates:
                            raw_text = candidates[0]["content"]["parts"][0]["text"]
                            parsed = parse_json_safely(raw_text)
                            if parsed:
                                return parsed
                    else:
                        resp_text = await response.text()
                        # Agar 403 yoki 404 bo'lsa keyingi modelni sinab ko'radi
                        continue
        except Exception as e:
            print(f"Gemini so'rovida xatolik ({model}): {e}")
            continue

    return None

async def analyze_with_openai(text: str) -> Optional[Dict[str, Any]]:
    """OpenAI API orqali tahlil qilish"""
    if not OPENAI_API_KEY:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                if response.status == 200:
                    result = await response.json()
                    raw_text = result["choices"][0]["message"]["content"]
                    return parse_json_safely(raw_text)
    except Exception as e:
        print(f"OpenAI xatolik: {e}")
    return None

def parse_json_safely(text: str) -> Optional[Dict[str, Any]]:
    """JSON matnini ajratib olish"""
    try:
        clean = text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]
        return json.loads(clean.strip())
    except Exception:
        # Regex orqali qidirish
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return None

async def process_user_text_with_ai(text: str) -> Dict[str, Any]:
    """AI orqali tahlil qilish (muvaffaqiyatsiz bo'lsa aqlli lokal tahlil)"""
    res = None
    if GEMINI_API_KEY:
        res = await analyze_with_gemini(text)
    elif OPENAI_API_KEY:
        res = await analyze_with_openai(text)

    if res and "action" in res:
        return res

    # AI javob bermasa yoki ruxsat yo'q bo'lsa, lokal tahlilchi
    return fallback_local_analyzer(text)

def fallback_local_analyzer(text: str) -> Dict[str, Any]:
    """Lokal tahlilchi: qarz, tovar va hisobotlarni tabiiy tildan ajratib oladi"""
    t = text.lower()

    # 1. Tovarni tahlil qilishga urinish (agar kod, dona, tan/sotuv narxlar kelsa)
    # Masalan: "Kodi 55, sumka, 10 dona, tan 50000, sotish 75000"
    if any(k in t for k in ["kod", "artikul", "tovar", "tan narx", "sotuv", "dona", "ta"]):
        numbers = [float(n) for n in re.findall(r'\b\d+(?:\.\d+)?\b', text)]
        code_match = re.search(r'(?:kod[i:]?|artikul[:\s]?)\s*([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        code = code_match.group(1) if code_match else (str(int(numbers[0])) if numbers else "001")

        # Agar narxlar sonlari yetarli bo'lsa
        if len(numbers) >= 3:
            # odatda: soni, tan narxi, sotuv narxi
            qty = numbers[0] if not code_match else (numbers[0] if str(int(numbers[0])) != code else (numbers[1] if len(numbers) > 1 else 1))
            cost = numbers[-2]
            sale = numbers[-1]
            return {
                "action": "add_product",
                "data": {
                    "code": code,
                    "name": "Tovar " + code,
                    "quantity": qty,
                    "cost_price": cost,
                    "sale_price": sale
                },
                "message": f"Tovar saqlandi: Kod {code}"
            }

    # 2. Qarzni tahlil qilishga urinish
    # Masalan: "Ali 150000 qarz oldi" yoki "Akmal 200 ming qarz"
    if any(k in t for k in ["qarz", "nasiya"]):
        # Summani topish
        sum_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(ming|mln)?', t)
        if sum_match:
            amount = float(sum_match.group(1).replace(",", "."))
            unit = sum_match.group(2)
            if unit == "ming" or ("ming" in t and amount < 1000):
                amount *= 1000
            elif unit == "mln" or "mln" in t:
                amount *= 1000000

            # Ismni ajratish (birinchi so'z)
            words = text.strip().split()
            debtor = words[0] if words else "Noma'lum"
            return {
                "action": "add_debt",
                "data": {
                    "debtor_name": debtor,
                    "amount": amount,
                    "description": text
                },
                "message": f"Qarz saqlandi: {debtor} - {amount:,.0f} so'm"
            }

    # 3. Hisobot so'rash
    if any(k in t for k in ["hisobot", "statistika", "qarzlarim", "tovarlarim"]):
        return {
            "action": "get_stats",
            "data": {},
            "message": "Hisobot"
        }

    # 4. Oddiy suhbat / yordam
    return {
        "action": "chat",
        "data": {},
        "message": (
            "🤖 <b>Aqlli Hisobchi Bot</b>\n\n"
            "Siz quyidagi amallarni bajarishingiz mumkin:\n"
            "🔹 <b>Tovar qo'shish:</b> Tugmani bosing yoki yozing: <i>«Kodi 101, Sumka, 10 dona, tan narxi 50000, sotish 80000»</i>\n"
            "🔹 <b>Qarz yozish:</b> Tugmani bosing yoki yozing: <i>«Dilshod 200 ming qarz oldi»</i>\n"
            "🔹 <b>Hisobot:</b> <i>«Hisobot»</i> deb yozing yoki tugmadan foydalaning!"
        )
    }
