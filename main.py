from fastapi import FastAPI
import sqlite3
from aiogram import Bot
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

# ===== DB =====
def get_db():
    return sqlite3.connect("db.sqlite3")

# ===== AUTH =====
ADMIN_TOKEN = "SECRET123"

# ===== GET CLIENTS =====
@app.get("/clients")
def get_clients(token: str):
    if token != ADMIN_TOKEN:
        return {"error": "unauthorized"}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, full_name, phone FROM users")
    data = cursor.fetchall()

    conn.close()

    return {"clients": data}

# ===== ADD TRACKS =====
@app.post("/add-tracks")
def add_tracks(token: str, tracks: str, date: str):
    if token != ADMIN_TOKEN:
        return {"error": "unauthorized"}

    conn = get_db()
    cursor = conn.cursor()

    track_list = tracks.split("\n")

    for t in track_list:
        t = t.strip()
        if t:
            cursor.execute(
                "INSERT OR IGNORE INTO tracks (track_code, status, date) VALUES (?, ?, ?)",
                (t, "На складе", date)
            )

    conn.commit()
    conn.close()

    return {"status": "ok"}

# ===== BROADCAST =====
@app.post("/broadcast")
async def broadcast(token: str, message: str):
    if token != ADMIN_TOKEN:
        return {"error": "unauthorized"}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT tg_id FROM users")
    users = cursor.fetchall()

    for user in users:
        try:
            await bot.send_message(user[0], message)
        except:
            pass

    conn.close()

    return {"status": "sent"}
