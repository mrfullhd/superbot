from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from utils.helpers import format_bytes
import shutil
from pathlib import Path
import config

async def latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... پیاده‌سازی
    await update.message.reply_text("📁 آخرین فایل: ...")

async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_dir = Path(config.DOWNLOAD_PATH) / str(user_id)
    
    if not user_dir.exists():
        await update.message.reply_text("📭 فایلی نیست")
        return
    
    files = list(user_dir.glob("**/*"))
    files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:20]
    
    if not files:
        await update.message.reply_text("📭 فایلی نیست")
        return
    
    text = "📂 **فایل‌ها:**\n"
    for f in files:
        text += f"📄 `{format_bytes(f.stat().st_size)}` - {f.name[:50]}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = db.get_history(user_id, 10)
    
    if not history:
        await update.message.reply_text("📭 تاریخچه خالی")
        return
    
    text = "📋 **تاریخچه:**\n"
    for item in history:
        text += f"✅ {item['type']} - {item['date']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def storage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    from core.google_drive import get_drive_service
    drive = get_drive_service(user_id)
    
    if drive:
        try:
            info = drive.get_storage_info(user_id)
            if info:
                text = (
                    f"💾 **Google Drive**\n"
                    f"🔵 `{format_bytes(info['usage'])}` / `{format_bytes(info['limit'])}`\n"
                    f"🟢 آزاد: `{format_bytes(info['limit'] - info['usage'])}`"
                )
                await update.message.reply_text(text, parse_mode="Markdown")
                return
        except:
            pass
    
    # Fallback: فضای سرور
    total, used, free = shutil.disk_usage("/")
    text = f"💾 **سرور**\n🟢 آزاد: `{format_bytes(free)}`"
    await update.message.reply_text(text, parse_mode="Markdown")
