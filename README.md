# 🤖 Aqlli Savdo va Qarz Hisobchisi Telegram Boti (AI bilan)

Ushbu Telegram bot savdo, do'kon va xususiy tadbirkorlik uchun mo'ljallangan bo'lib, ikkita asosiy vazifani va **Sun'iy Intellekt (AI)** orqali avtomatik tahlilni amalga oshiradi.

---

## 🌟 Asosiy Imkoniyatlar

### 1️⃣ Tovarlar hisobi (Inventar):
* **Maxsus raqam** (kod yoki artikul)
* **Tovar nomi**
* **Tovar soni** (dona/miqdor)
* **Tan narxi** (tannarx)
* **Sotuv narxi**
* **Foyda hisob-kitobi:** Har bir tovardan va umumiy kutilayotgan sof foydani avtomatik hisoblaydi.

### 2️⃣ Qarzlar daftari (Nasiya hisobi):
* Kim qarz olganligi (ism yoki telefon raqam)
* Qarz summasi
* Qarz izohi yoki qaytarish sanasi
* Bir bosishda qarzni **«To'landi»** deb belgilash yoki o'chirish.
* Umumiy to'lanmagan qarzlar summasini avtomatik chiqarish.

### 🧠 3️⃣ Sun'iy Intellekt (AI) Integratsiyasi:
* **Erkin matn tahlili:** Do'konda shoshilinch paytda tugmalarni bosib o'tirmasdan, oddiy xabar yozasiz.
  * *Misol 1:* `Kodi 55, Sport krossovka, 20 dona, tan narxi 120000, sotish narxi 175000` — AI buni tushunadi va tovarlar bazasiga kiritadi.
  * *Misol 2:* `Ali aka 250 ming qarz oldi, haftaga beradi` — AI buni tushunadi va qarzlar daftaringizga kiritadi.
* **Google Gemini (bepul)** yoki **OpenAI** modellari bilan ishlaydi.

---

## 📂 Loyiha Tuzilishi

```
tg hisobchi/
├── bot.py             # Asosiy Telegram bot kodi (aiogram 3)
├── database.py        # SQLite ma'lumotlar bazasi (asinxron aiosqlite)
├── ai_service.py      # Sun'iy intellekt tahlilchisi (Gemini / OpenAI)
├── keyboards.py       # Bot tugmalari va menyulari
├── config.py          # Sozlamalar va muhit o'zgaruvchilari
├── requirements.txt   # Kerakli Python kutubxonalari
├── .env               # Token va kalitlar saqlanadigan fayl
└── README.md          # Qo'llanma
```

---

## 🚀 Ishga Tushirish Yo'riqnomasi

### 1-qadam: Kutubxonalarni o'rnatish

Terminalda (PowerShell yoki CMD) quyidagi buyruqni ishga tushiring:
```bash
python -m pip install -r requirements.txt
```

### 2-qadam: Tokenlarni olish va sozlash

`.env` faylini oching va quyidagi qiymatlarni kiriting:

1. **Telegram Bot Token:**
   * Telegramda [@BotFather](https://t.me/BotFather) ga kiring.
   * `/newbot` buyrug'i orqali yangi bot yarating va berilgan tokenni oling.
   * `.env` faylida `BOT_TOKEN=...` qatoriga yozing.

2. **Google Gemini API Key (Mutlaqo bepul):**
   * [Google AI Studio](https://aistudio.google.com/) saytiga kiring.
   * **«Get API key»** tugmasini bosib bepul kalit yarating.
   * `.env` faylida `GEMINI_API_KEY=...` qatoriga yozing.

*(Eslatma: Agar AI kaliti kiritilmasa ham bot oddiy tugmalar orqali to'liq ishlayveradi!)*

### 3-qadam: Botni ishga tushirish

```bash
python bot.py
```

Endi Telegramda o'z botingizga kiring va `/start` buyrug'ini bosing! 🎉
