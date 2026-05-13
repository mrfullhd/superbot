from telegram import Update
from telegram.ext import ContextTypes
from core.google_drive import get_drive_service
from core.database import db
from utils.helpers import format_bytes, sanitize_name
from pathlib import Path
import time

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.reply_to_message:
        message = update.message.reply_to_message
        file_id = None
        file_name = "unknown"
        file_size = 0
        
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name or "file"
            file_size = message.document.file_size
        elif message.video:
            file_id = message.video.file_id
            file_name = message.video.file_name or f"video_{int(time.time())}.mp4"
            file_size = message.video.file_size
        elif message.audio:
            file_id = message.audio.file_id
            file_name = message.audio.file_name or f"audio_{int(time.time())}.mp3"
            file_size = message.audio.file_size
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_name = f"photo_{int(time.time())}.jpg"
            file_size = message.photo[-1].file_size
        elif message.voice:
            file_id = message.voice.file_id
            file_name = f"voice_{int(time.time())}.ogg"
            file_size = message.voice.file_size
        else:
            await update.message.reply_text("❌ نوع فایل پشتیبانی نمی‌شود")
            return
        
        msg = await update.message.reply_text("📤 در حال آپلود...")
        
        try:
            # دانلود فایل از تلگرام
            file_obj = await context.bot.get_file(file_id)
            safe_name = sanitize_name(file_name)
            temp_path = Path("downloads") / str(user_id) / safe_name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            
            await file_obj.download_to_drive(str(temp_path))
            
            # آپلود به Google Drive
            drive = get_drive_service(user_id)
            if drive:
                drive.upload_file(user_id, temp_path)
                await msg.edit_text(
                    f"✅ آپلود شد!\n📁 `{safe_name}`\n📏 `{format_bytes(file_size)}`\n💾 Google Drive",
                    parse_mode="Markdown"
                )
            else:
                await msg.edit_text(
                    f"✅ ذخیره موقت شد!\n📁 `{safe_name}`\n📏 `{format_bytes(file_size)}`\n"
                    f"⚠️ برای آپلود به Drive، `/login` بزنید.",
                    parse_mode="Markdown"
                )
            
            db.add_history(user_id, "upload", f"Telegram: {safe_name}", str(temp_path), file_size)
            db.update_stats(user_id, "upload", file_size)
            
            # پاکسازی
            try:
                temp_path.unlink()
            except:
                pass
                
        except Exception as e:
            await msg.edit_text(f"❌ `{str(e)[:200]}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("📤 روی فایل ریپلای کنید + `/up`", parse_mode="Markdown")

async def handle_caption_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فایل با کپشن /up"""
    caption = update.message.caption or ""
    if "/up" in caption:
        # شبیه‌سازی ریپلای
        await upload_command(update, context)
