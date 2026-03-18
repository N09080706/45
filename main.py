from fastapi import FastAPI
import sqlite3
import os
from aiogram import Bot

app = FastAPI()
@app.get("/")
def root():
    return {"status": "API WORKING"}
    
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

ADMIN_TOKEN = "SECRET123"

def get_db():
    return sqlite3.connect("db.sqlite3")

@app.get("/")
def root():
    return {"status": "API WORKING"}

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

@app.post("/add-tracks")
def add_tracks(token: str, tracks: str, date: str):
    if token != ADMIN_TOKEN:
        return {"error": "unauthorized"}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track_code TEXT UNIQUE,
        status TEXT,
        date TEXT
    )
    """)

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
