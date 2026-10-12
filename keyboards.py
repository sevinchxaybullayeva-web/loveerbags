from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

def get_main_menu() -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari"""
    keyboard = [
        [
            KeyboardButton(text="📦 Tovar qo'shish"),
            KeyboardButton(text="📋 Tovarlar ro'yxati")
        ],
        [
            KeyboardButton(text="📝 Qarz yozish"),
            KeyboardButton(text="👥 Qarzlar daftari")
        ],
        [
            KeyboardButton(text="📊 Umumiy hisobot"),
            KeyboardButton(text="🤖 AI haqida / Yordam")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )

def get_cancel_menu() -> ReplyKeyboardMarkup:
    """Jarayonni bekor qilish tugmasi"""
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_debt_item_keyboard(debt_id: int) -> InlineKeyboardMarkup:
    """Qarz elementi uchun tugmalar (to'landi / o'chirish)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Qarz to'landi", 
                    callback_data=f"pay_debt:{debt_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 O'chirish", 
                    callback_data=f"del_debt:{debt_id}"
                )
            ]
        ]
    )

def get_product_item_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Tovar uchun boshqaruv tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Tovarni o'chirish", 
                    callback_data=f"del_prod:{product_id}"
                )
            ]
        ]
    )
