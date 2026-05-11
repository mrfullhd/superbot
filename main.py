import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import config
from core.database import db
from handlers.youtube import yt_command, mp3_command
from handlers.upload import upload_command, handle_caption_upload
from handlers.info import files_command, storage_command

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.add_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    await update.message.reply_text(
        f"🤖 **AzuDl Bot**\n\n"
        f"📥 `/yt URL` - دانلود یوتیوب\n"
        f"📥 `/mp3 URL` - دانلود MP3\n"
        f"📤 `/up` - آپلود فایل به سرور\n"
        f"📊 `/files` - `/storage`",
        parse_mode="Markdown"
    )

def main():
    # ساخت پوشه‌ها
    for d in ["downloads", "logs", "cookies"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    # ساخت اپلیکیشن
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yt", yt_command))
    app.add_handler(CommandHandler("mp3", mp3_command))
    app.add_handler(CommandHandler("up", upload_command))
    app.add_handler(CommandHandler("files", files_command))
    app.add_handler(CommandHandler("storage", storage_command))
    app.add_handler(MessageHandler(filters.CAPTION & filters.Regex(r'^/up'), handle_caption_upload))
    
    print("✅ Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
