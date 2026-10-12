import aiosqlite
from typing import List, Optional, Dict, Any
from config import DB_PATH

async def init_db():
    """Ma'lumotlar bazasi va jadvallarni yaratish"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Tovarlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                name TEXT,
                quantity REAL NOT NULL,
                cost_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Qarzlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                debtor_name TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'unpaid',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP
            )
        """)
        await db.commit()

# ================= TOVARLAR FUNKSIYALARI =================

async def add_or_update_product(
    user_id: int, 
    code: str, 
    name: str, 
    quantity: float, 
    cost_price: float, 
    sale_price: float
) -> Dict[str, Any]:
    """Yangi tovar qo'shish yoki mavjud tovar sonini oshirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM products WHERE user_id = ? AND code = ?",
            (user_id, code.strip())
        )
        existing = await cursor.fetchone()

        if existing:
            new_qty = existing["quantity"] + quantity
            await db.execute(
                """
                UPDATE products 
                SET quantity = ?, name = COALESCE(?, name), cost_price = ?, sale_price = ?
                WHERE id = ?
                """,
                (new_qty, name if name else existing["name"], cost_price, sale_price, existing["id"])
            )
            await db.commit()
            return {
                "status": "updated",
                "id": existing["id"],
                "code": code,
                "name": name or existing["name"],
                "quantity": new_qty,
                "cost_price": cost_price,
                "sale_price": sale_price
            }
        else:
            cur = await db.execute(
                """
                INSERT INTO products (user_id, code, name, quantity, cost_price, sale_price)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, code.strip(), name, quantity, cost_price, sale_price)
            )
            await db.commit()
            return {
                "status": "created",
                "id": cur.lastrowid,
                "code": code,
                "name": name,
                "quantity": quantity,
                "cost_price": cost_price,
                "sale_price": sale_price
            }

async def get_products(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Barcha tovarlar ro'yxatini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM products WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_product_by_code(user_id: int, code: str) -> Optional[Dict[str, Any]]:
    """Maxsus kodi bo'yicha tovar qidirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM products WHERE user_id = ? AND code = ?",
            (user_id, code.strip())
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

async def delete_product(user_id: int, product_id: int) -> bool:
    """Tovarni o'chirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM products WHERE user_id = ? AND id = ?",
            (user_id, product_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def get_product_stats(user_id: int) -> Dict[str, Any]:
    """Ombor statistikasi (jami tovarlar, sarmoya, kutilayotgan foyda)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT 
                COUNT(*) as total_types,
                COALESCE(SUM(quantity), 0) as total_items,
                COALESCE(SUM(quantity * cost_price), 0) as total_cost,
                COALESCE(SUM(quantity * sale_price), 0) as total_sale
            FROM products WHERE user_id = ?
            """,
            (user_id,)
        )
        row = await cursor.fetchone()
        stats = dict(row)
        stats["expected_profit"] = stats["total_sale"] - stats["total_cost"]
        return stats

# ================= QARZLAR FUNKSIYALARI =================

async def add_debt(user_id: int, debtor_name: str, amount: float, description: str = "") -> int:
    """Yangi qarz qo'shish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO debts (user_id, debtor_name, amount, description, status)
            VALUES (?, ?, ?, ?, 'unpaid')
            """,
            (user_id, debtor_name.strip(), amount, description.strip() if description else "")
        )
        await db.commit()
        return cursor.lastrowid

async def get_debts(user_id: int, status: str = "unpaid") -> List[Dict[str, Any]]:
    """Qarzlar ro'yxatini olish (unpaid yoki paid)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status == "all":
            cursor = await db.execute(
                "SELECT * FROM debts WHERE user_id = ? ORDER BY status ASC, id DESC",
                (user_id,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM debts WHERE user_id = ? AND status = ? ORDER BY id DESC",
                (user_id, status)
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_debt_by_id(user_id: int, debt_id: int) -> Optional[Dict[str, Any]]:
    """Qarzni ID bo'yicha olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM debts WHERE user_id = ? AND id = ?",
            (user_id, debt_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

async def mark_debt_as_paid(user_id: int, debt_id: int) -> bool:
    """Qarzni to'landi deb belgilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE debts 
            SET status = 'paid', paid_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND id = ?
            """,
            (user_id, debt_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def delete_debt(user_id: int, debt_id: int) -> bool:
    """Qarzni o'chirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM debts WHERE user_id = ? AND id = ?",
            (user_id, debt_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def get_debt_stats(user_id: int) -> Dict[str, Any]:
    """Qarzlar statistikasi"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT 
                COUNT(*) as total_unpaid_count,
                COALESCE(SUM(amount), 0) as total_unpaid_amount
            FROM debts WHERE user_id = ? AND status = 'unpaid'
            """,
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row)
