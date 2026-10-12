import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import config
import database as db
import keyboards as kb
from ai_service import process_user_text_with_ai

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Loglarni sozlash
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# FSM (Holatlar) klasslari
class AddProductStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_name = State()
    waiting_for_quantity = State()
    waiting_for_cost_price = State()
    waiting_for_sale_price = State()

class AddDebtStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_description = State()

def format_money(amount: float) -> str:
    """Pul miqdorini chiroyli formatda chiqarish (masalan: 150 000 so'm)"""
    return f"{amount:,.0f}".replace(",", " ") + " so'm"

# ================= HANDLERS =================

dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start buyrug'i"""
    await state.clear()
    text = (
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        "🤖 <b>Aqlli Savdo va Qarz Hisobchisi Botiga xush kelibsiz!</b>\n\n"
        "Men quyidagi 2 ta asosiy vazifani bajara olaman:\n"
        "1️⃣ <b>Tovarlar hisobi:</b> Maxsus raqami (artikul), soni, tan narxi va sotuv narxi.\n"
        "2️⃣ <b>Qarzlar daftari:</b> Qarzdorlar ro'yxati, summa va qarz holatini yuritish.\n\n"
        "🧠 <b>AI Xususiyati:</b> Siz menga shunchaki oddiy xabar yozishingiz ham mumkin!\n"
        "<i>Masalan:</i>\n"
        "• <i>«Kodi 777, Ko'ylak, 10 dona, tan narxi 60000, sotish 95000»</i>\n"
        "• <i>«Ali 300 ming qarz oldi, haftaga beradi»</i>\n\n"
        "Kerakli bo'limni tanlang yoki xabar yozing 👇"
    )
    await message.answer(text, reply_markup=kb.get_main_menu())

@dp.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    """Har qanday jarayonni bekor qilish"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await message.answer("❌ Jarayon bekor qilindi.", reply_markup=kb.get_main_menu())

# ----------------- TOVAR QO'SHISH (FSM) -----------------

@dp.message(F.text == "📦 Tovar qo'shish")
async def start_add_product(message: Message, state: FSMContext):
    await state.set_state(AddProductStates.waiting_for_code)
    await message.answer(
        "📦 Tovarning <b>maxsus raqamini (kodi yoki artikul)</b> kiriting:\n"
        "(Masalan: <code>101</code> yoki <code>A-24</code>)",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddProductStates.waiting_for_code)
async def process_product_code(message: Message, state: FSMContext):
    code = message.text.strip()
    await state.update_data(code=code)
    await state.set_state(AddProductStates.waiting_for_name)
    await message.answer(
        "🏷 Tovar <b>nomini</b> kiriting (yoki o'tkazib yuborish uchun - belgisini yuboring):",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddProductStates.waiting_for_name)
async def process_product_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if name == "-":
        name = "Nomsiz tovar"
    await state.update_data(name=name)
    await state.set_state(AddProductStates.waiting_for_quantity)
    await message.answer(
        "🔢 Tovar <b>sonini (miqdorini)</b> kiriting (masalan: <code>15</code>):",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddProductStates.waiting_for_quantity)
async def process_product_quantity(message: Message, state: FSMContext):
    try:
        qty = float(message.text.replace(",", ".").strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, musbat son kiriting (masalan: 10 yoki 2.5):")
        return

    await state.update_data(quantity=qty)
    await state.set_state(AddProductStates.waiting_for_cost_price)
    await message.answer(
        "💵 Tovarning <b>tan narxini</b> kiriting (masalan: <code>50000</code>):",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddProductStates.waiting_for_cost_price)
async def process_product_cost_price(message: Message, state: FSMContext):
    try:
        cost = float(message.text.replace(",", ".").replace(" ", "").strip())
        if cost < 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, to'g'ri narx kiriting (masalan: 50000):")
        return

    await state.update_data(cost_price=cost)
    await state.set_state(AddProductStates.waiting_for_sale_price)
    await message.answer(
        "💰 Tovarning <b>sotuv narxini</b> kiriting (masalan: <code>75000</code>):",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddProductStates.waiting_for_sale_price)
async def process_product_sale_price(message: Message, state: FSMContext):
    try:
        sale = float(message.text.replace(",", ".").replace(" ", "").strip())
        if sale < 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, to'g'ri narx kiriting (masalan: 75000):")
        return

    data = await state.get_data()
    await state.clear()

    res = await db.add_or_update_product(
        user_id=message.from_user.id,
        code=data["code"],
        name=data["name"],
        quantity=data["quantity"],
        cost_price=data["cost_price"],
        sale_price=sale
    )

    profit_per_item = sale - data["cost_price"]
    total_profit = profit_per_item * res["quantity"]

    status_str = "yangilandi (soni oshirildi)" if res["status"] == "updated" else "muvaffaqiyatli saqlandi"

    text = (
        f"✅ <b>Tovar {status_str}!</b>\n\n"
        f"🔢 <b>Maxsus raqam:</b> <code>{res['code']}</code>\n"
        f"🏷 <b>Nomi:</b> {res['name']}\n"
        f"📦 <b>Jami soni:</b> {res['quantity']} dona\n"
        f"💵 <b>Tan narxi:</b> {format_money(res['cost_price'])}\n"
        f"💰 <b>Sotuv narxi:</b> {format_money(res['sale_price'])}\n"
        f"📈 <b>Dona boshiga foyda:</b> {format_money(profit_per_item)}\n"
        f"🏆 <b>Kutilayotgan umumiy foyda:</b> {format_money(total_profit)}"
    )
    await message.answer(text, reply_markup=kb.get_main_menu())

# ----------------- TOVARLAR RO'YXATI -----------------

@dp.message(F.text == "📋 Tovarlar ro'yxati")
async def list_products_handler(message: Message):
    products = await db.get_products(message.from_user.id)
    if not products:
        await message.answer(
            "📭 Hozircha birorta ham tovar kiritilmagan.\n"
            "«📦 Tovar qo'shish» tugmasi orqali tovar kiriting.",
            reply_markup=kb.get_main_menu()
        )
        return

    text = "📋 <b>Sizning tovarlaringiz ro'yxati:</b>\n\n"
    for p in products:
        profit = (p['sale_price'] - p['cost_price']) * p['quantity']
        text += (
            f"🔹 <b>Kod:</b> <code>{p['code']}</code> | <b>{p['name']}</b>\n"
            f"   📦 Soni: {p['quantity']} ta\n"
            f"   💵 Tan: {format_money(p['cost_price'])} | 💰 Sotuv: {format_money(p['sale_price'])}\n"
            f"   📈 Foyda: {format_money(profit)}\n"
            f"   <i>O'chirish uchun: /del_prod_{p['id']}</i>\n"
            f"────────────────────\n"
        )
    await message.answer(text, reply_markup=kb.get_main_menu())

@dp.message(F.text.startswith("/del_prod_"))
async def delete_product_cmd(message: Message):
    try:
        prod_id = int(message.text.replace("/del_prod_", "").strip())
        success = await db.delete_product(message.from_user.id, prod_id)
        if success:
            await message.answer("🗑 Tovar muvaffaqiyatli o'chirildi!")
        else:
            await message.answer("⚠️ Tovar topilmadi yoki allaqachon o'chirilgan.")
    except Exception:
        await message.answer("⚠️ Xatolik yuz berdi.")

# ----------------- QARZ YOZISH (FSM) -----------------

@dp.message(F.text == "📝 Qarz yozish")
async def start_add_debt(message: Message, state: FSMContext):
    await state.set_state(AddDebtStates.waiting_for_name)
    await message.answer(
        "👤 <b>Kim qarz oldi?</b> (Qarzdorning ismi yoki telefon raqami):\n"
        "(Masalan: <code>Alisher aka</code> yoki <code>Dilshod +998901234567</code>)",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddDebtStates.waiting_for_name)
async def process_debt_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(debtor_name=name)
    await state.set_state(AddDebtStates.waiting_for_amount)
    await message.answer(
        "💰 <b>Qarz summasini</b> kiriting (masalan: <code>150000</code>):",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddDebtStates.waiting_for_amount)
async def process_debt_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", ".").replace(" ", "").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, musbat summa kiriting (masalan: 200000):")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddDebtStates.waiting_for_description)
    await message.answer(
        "📝 <b>Izoh yoki muddat</b> kiriting (ixtiyoriy, bo'sh qoldirish uchun - yozing):\n"
        "(Masalan: <i>Shanba kuni beradi</i> yoki <i>2 juft poyabzal uchun</i>)",
        reply_markup=kb.get_cancel_menu()
    )

@dp.message(AddDebtStates.waiting_for_description)
async def process_debt_description(message: Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    data = await state.get_data()
    await state.clear()

    debt_id = await db.add_debt(
        user_id=message.from_user.id,
        debtor_name=data["debtor_name"],
        amount=data["amount"],
        description=desc
    )

    text = (
        f"✅ <b>Qarz muvaffaqiyatli saqlandi!</b>\n\n"
        f"👤 <b>Qarzdor:</b> {data['debtor_name']}\n"
        f"💰 <b>Summa:</b> {format_money(data['amount'])}\n"
        f"📝 <b>Izoh:</b> {desc if desc else 'Mavjud emas'}"
    )
    await message.answer(text, reply_markup=kb.get_main_menu())

# ----------------- QARZLAR DAFTARI -----------------

@dp.message(F.text == "👥 Qarzlar daftari")
async def list_debts_handler(message: Message):
    debts = await db.get_debts(message.from_user.id, status="unpaid")
    if not debts:
        await message.answer(
            "🎉 <b>Ajoyib!</b> Hozircha to'lanmagan qarzlar yo'q.",
            reply_markup=kb.get_main_menu()
        )
        return

    stats = await db.get_debt_stats(message.from_user.id)
    summary_text = (
        f"👥 <b>QARZLAR RO'YXATI (To'lanmagan):</b>\n"
        f"📊 Jami qarzdorlar: <b>{stats['total_unpaid_count']} kishi</b>\n"
        f"💰 Jami to'lanmagan summa: <b>{format_money(stats['total_unpaid_amount'])}</b>\n"
        f"────────────────────"
    )
    await message.answer(summary_text)

    for d in debts:
        desc_line = f"\n📝 Izoh: {d['description']}" if d['description'] else ""
        date_line = f"\n📅 Sana: {d['created_at'][:16]}"
        item_text = (
            f"👤 <b>{d['debtor_name']}</b>\n"
            f"💵 Summa: <b>{format_money(d['amount'])}</b>"
            f"{desc_line}{date_line}"
        )
        await message.answer(item_text, reply_markup=kb.get_debt_item_keyboard(d['id']))

@dp.callback_query(F.data.startswith("pay_debt:"))
async def cb_pay_debt(callback: CallbackQuery):
    debt_id = int(callback.data.split(":")[1])
    success = await db.mark_debt_as_paid(callback.from_user.id, debt_id)
    if success:
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ <b>QARZ TO'LANDI deb belgilandi!</b>"
        )
        await callback.answer("Qarz to'landi deb belgilandi!")
    else:
        await callback.answer("Xatolik yuz berdi!", show_alert=True)

@dp.callback_query(F.data.startswith("del_debt:"))
async def cb_del_debt(callback: CallbackQuery):
    debt_id = int(callback.data.split(":")[1])
    success = await db.delete_debt(callback.from_user.id, debt_id)
    if success:
        await callback.message.edit_text("🗑 <b>Qarz o'chirildi.</b>")
        await callback.answer("O'chirildi!")
    else:
        await callback.answer("Xatolik yuz berdi!", show_alert=True)

# ----------------- STATISTIKA VA YORDAM -----------------

@dp.message(F.text == "📊 Umumiy hisobot")
async def report_handler(message: Message):
    user_id = message.from_user.id
    p_stats = await db.get_product_stats(user_id)
    d_stats = await db.get_debt_stats(user_id)

    text = (
        "📊 <b>UMUMIY BIZNES HISOBOTI</b>\n\n"
        "📦 <b>Tovarlar hisobi:</b>\n"
        f"• Tovar turlari: <b>{p_stats['total_types']} xil</b>\n"
        f"• Jami tovar soni: <b>{p_stats['total_items']} dona</b>\n"
        f"• Kiritilgan sarmoya (tan narx): <b>{format_money(p_stats['total_cost'])}</b>\n"
        f"• Sotuv qiymati: <b>{format_money(p_stats['total_sale'])}</b>\n"
        f"• 📈 Kutilayotgan sof foyda: <b>{format_money(p_stats['expected_profit'])}</b>\n\n"
        "👥 <b>Qarzlar hisobi:</b>\n"
        f"• Qarzdorlar soni: <b>{d_stats['total_unpaid_count']} kishi</b>\n"
        f"• Qaytarilishi kerak bo'lgan summa: <b>{format_money(d_stats['total_unpaid_amount'])}</b>\n"
    )
    await message.answer(text, reply_markup=kb.get_main_menu())

@dp.message(F.text == "🤖 AI haqida / Yordam")
async def ai_help_handler(message: Message):
    text = (
        "🤖 <b>Sun'iy Intellekt (AI) qanday ishlaydi?</b>\n\n"
        "Siz tugmalarni bosib o'tirmasdan, botga xuddi do'stingizga yozgandek erkin matn yozishingiz mumkin. "
        "AI uni tushunadi va o'zi kerakli bo'limga saqlaydi!\n\n"
        "<b>Misollar:</b>\n"
        "1️⃣ <b>Tovar qo'shish:</b>\n"
        "<i>«Kodi 55, Sport krossovka, 20 dona, tan narxi 120000, sotish narxi 175000»</i>\n\n"
        "2️⃣ <b>Qarz yozish:</b>\n"
        "<i>«Javohir 450 ming qarz oldi, payshanba kuni olib keladi»</i>\n\n"
        "3️⃣ <b>Hisobot:</b>\n"
        "<i>«Menda qancha qarz bor?»</i> yoki <i>«Tovarlarim haqida hisobot ber»</i>\n\n"
        "Hozir sinab ko'ring! Istalgan xabarni yozib yuboring 🚀"
    )
    await message.answer(text, reply_markup=kb.get_main_menu())

# ----------------- AI ERKIN MATN HANDLERI -----------------

@dp.message(F.text)
async def ai_text_message_handler(message: Message, state: FSMContext):
    """Foydalanuvchi erkin yozgan xabarlarni AI orqali tahlil qilish"""
    # Agar foydalanuvchi biron FSM bosqichida bo'lsa, bu handlerga tushmasin
    current_state = await state.get_state()
    if current_state is not None:
        return

    # "Typing..." statusi yuborish
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    ai_result = await process_user_text_with_ai(message.text)
    action = ai_result.get("action")
    data = ai_result.get("data", {})

    if action == "add_product":
        code = str(data.get("code", "000"))
        name = data.get("name", "Nomsiz tovar")
        qty = float(data.get("quantity", 1))
        cost = float(data.get("cost_price", 0))
        sale = float(data.get("sale_price", 0))

        res = await db.add_or_update_product(
            user_id=message.from_user.id,
            code=code,
            name=name,
            quantity=qty,
            cost_price=cost,
            sale_price=sale
        )
        profit_per_item = sale - cost
        total_profit = profit_per_item * res["quantity"]

        text = (
            f"🤖 <b>AI Tovarni saqladi!</b>\n\n"
            f"🔢 <b>Maxsus raqam:</b> <code>{res['code']}</code>\n"
            f"🏷 <b>Nomi:</b> {res['name']}\n"
            f"📦 <b>Soni:</b> {res['quantity']} dona\n"
            f"💵 <b>Tan narxi:</b> {format_money(res['cost_price'])}\n"
            f"💰 <b>Sotuv narxi:</b> {format_money(res['sale_price'])}\n"
            f"📈 <b>Dona boshiga foyda:</b> {format_money(profit_per_item)}\n"
            f"🏆 <b>Jami kutilayotgan foyda:</b> {format_money(total_profit)}"
        )
        await message.answer(text, reply_markup=kb.get_main_menu())

    elif action == "add_debt":
        debtor = data.get("debtor_name", "Noma'lum")
        amount = float(data.get("amount", 0))
        desc = data.get("description", "")

        await db.add_debt(
            user_id=message.from_user.id,
            debtor_name=debtor,
            amount=amount,
            description=desc
        )

        text = (
            f"🤖 <b>AI Qarzni saqladi!</b>\n\n"
            f"👤 <b>Qarzdor:</b> {debtor}\n"
            f"💰 <b>Summa:</b> {format_money(amount)}\n"
            f"📝 <b>Izoh:</b> {desc if desc else 'Mavjud emas'}"
        )
        await message.answer(text, reply_markup=kb.get_main_menu())

    elif action == "get_stats":
        await report_handler(message)

    else:
        # Oddiy javob yoki tushuntirish
        reply_msg = ai_result.get("message", "Xabaringiz qabul qilindi.")
        await message.answer(reply_msg, reply_markup=kb.get_main_menu())

# ================= ASOSIY ISHGA TUSHIRISH =================

import os
from aiohttp import web

async def start_dummy_web_server(port: int):
    """Bulutli serverlar (Railway/Render) port talab qilganda javob beruvchi yengil server"""
    app = web.Application()
    async def handle_ping(request):
        return web.Response(text="Bot is running!")
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Web health-check server ishga tushdi: port {port}")

async def main():
    if not config.BOT_TOKEN:
        print("❌ XATOLIK: BOT_TOKEN ko'rsatilmagan! .env faylida BOT_TOKEN ni belgilang.")
        return

    # Bulutli platforma (Railway/Render) PORT berganda web serverni yoqish
    port_env = os.getenv("PORT")
    if port_env:
        try:
            await start_dummy_web_server(int(port_env))
        except Exception as e:
            print(f"Web server xatosi: {e}")

    # Bazani ishga tushirish
    await db.init_db()
    print("✅ Ma'lumotlar bazasi tayyor.")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    print("🚀 Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
