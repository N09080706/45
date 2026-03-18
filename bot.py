import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import os

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ===== DB =====
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER UNIQUE,
    full_name TEXT,
    phone TEXT UNIQUE,
    language TEXT DEFAULT 'ru'
)
""")
conn.commit()

def user_exists(tg_id):
    cursor.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
    return cursor.fetchone()

def phone_exists(phone):
    cursor.execute("SELECT * FROM users WHERE phone=?", (phone,))
    return cursor.fetchone()

def add_user(tg_id, full_name, phone):
    cursor.execute(
        "INSERT INTO users (tg_id, full_name, phone) VALUES (?, ?, ?)",
        (tg_id, full_name, phone)
    )
    conn.commit()

def get_user_id(tg_id):
    cursor.execute("SELECT id FROM users WHERE tg_id=?", (tg_id,))
    return cursor.fetchone()

# ===== FSM =====
class Register(StatesGroup):
    full_name = State()
    phone = State()

# ===== KEYBOARD =====
kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(KeyboardButton("🏠 Получить адрес"))

# ===== START =====
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    if user_exists(msg.from_user.id):
        await msg.answer("✅ Вы уже зарегистрированы!", reply_markup=kb)
        return

    await msg.answer("📝 Введите ФИО:")
    await Register.full_name.set()

# ===== NAME =====
@dp.message_handler(state=Register.full_name)
async def get_name(msg: types.Message, state: FSMContext):
    await state.update_data(full_name=msg.text)
    await msg.answer("📱 Введите номер телефона:")
    await Register.phone.set()

# ===== PHONE =====
@dp.message_handler(state=Register.phone)
async def get_phone(msg: types.Message, state: FSMContext):
    phone = msg.text

    if phone_exists(phone):
        await msg.answer("❌ Этот номер уже зарегистрирован!")
        return

    data = await state.get_data()

    add_user(msg.from_user.id, data['full_name'], phone)

    await msg.answer("✅ Регистрация завершена!", reply_markup=kb)
    await state.finish()

# ===== ADDRESS =====
@dp.message_handler(lambda m: m.text == "🏠 Получить адрес")
async def address(msg: types.Message):
    user = get_user_id(msg.from_user.id)

    if not user:
        await msg.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    user_id = user[0]

    text = f"""📦 Ваш адрес:

X7BOX/{user_id}
18042568166 浙江省金华市义乌市 义乌市福田街道物华路68号  肖志华  Dabex 0077 / X7BOX/{user_id}
"""

    await msg.answer(text)

if __name__ == "__main__":
    executor.start_polling(dp)
