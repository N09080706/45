import os
import asyncio
import aiohttp
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)


# ====== СКАЧИВАНИЕ ЧЕРЕЗ YT-DLP ======
async def download_video(url):
    loop = asyncio.get_event_loop()

    def ytdlp_download():
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_PATH}/%(title)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    return await loop.run_in_executor(None, ytdlp_download)


# ====== СКАЧИВАНИЕ ПРЯМОГО ФАЙЛА ======
async def download_direct(url):
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or "file"

    filepath = os.path.join(DOWNLOAD_PATH, filename)

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP ошибка: {resp.status}")

            with open(filepath, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    f.write(chunk)

    return filepath


# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📥 Отправь ссылку:\n"
        "• YouTube / TikTok / Instagram / Pinterest\n"
        "• или прямую ссылку на файл"
    )


# ====== ОБРАБОТКА ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    msg = await update.message.reply_text("⏳ Скачиваю...")

    file_path = None

    try:
        # ===== СНАЧАЛА ПРОБУЕМ YT-DLP =====
        try:
            file_path = await download_video(url)
        except Exception:
            # ===== ЕСЛИ НЕ ПОЛУЧИЛОСЬ → ПРЯМАЯ ССЫЛКА =====
            file_path = await download_direct(url)

        size = os.path.getsize(file_path)

        # лимит Telegram
        if size > 49 * 1024 * 1024:
            await msg.edit_text("⚠️ Файл слишком большой (>50MB)")
            os.remove(file_path)
            return

        ext = file_path.lower()

        with open(file_path, "rb") as f:
            if ext.endswith((".mp4", ".mov")):
                await update.message.reply_video(video=f)
            elif ext.endswith(".mp3"):
                await update.message.reply_audio(audio=f)
            elif ext.endswith((".jpg", ".jpeg", ".png")):
                await update.message.reply_photo(photo=f)
            else:
                await update.message.reply_document(document=f)

        # ===== АВТО УДАЛЕНИЕ =====
        os.remove(file_path)

        await msg.delete()

    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        await msg.edit_text(f"❌ Не удалось скачать\n\n{str(e)[:300]}")


# ====== ЗАПУСК ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
