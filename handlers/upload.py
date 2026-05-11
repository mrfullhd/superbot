import time
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from core.uploader import download_from_telegram
from utils.helpers import format_bytes, sanitize_name, make_progress_bar

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "📤 روی فایل ریپلای کنید + `/up`\n💪 بدون محدودیت حجم با MTProto",
            parse_mode="Markdown"
        )
        return
    
    message = update.message.reply_to_message
    msg = await update.message.reply_text("📤 شروع آپلود...")
    
    temp_path = None
    
    try:
        # تشخیص فایل
        file_name = "unknown"
        file_size = 0
        
        if message.document:
            file_name = message.document.file_name or "document"
            file_size = message.document.file_size
        elif message.video:
            file_name = message.video.file_name or f"video_{int(time.time())}.mp4"
            file_size = message.video.file_size
        elif message.audio:
            file_name = message.audio.file_name or f"audio_{int(time.time())}.mp3"
            file_size = message.audio.file_size
        elif message.photo:
            file_name = f"photo_{int(time.time())}.jpg"
            file_size = message.photo[-1].file_size
        else:
            await msg.edit_text("❌ نوع فایل پشتیبانی نمی‌شود")
            return
        
        safe_name = sanitize_name(file_name)
        temp_path = Path("downloads") / str(user_id) / safe_name
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Progress bar state
        progress_state = {"current": 0, "total": file_size, "done": False}
        
        def progress_callback(current, total):
            progress_state["current"] = current
            progress_state["total"] = total
        
        # آپدیت کننده progress
        async def update_progress():
            last = 0
            while not progress_state["done"]:
                current = progress_state["current"]
                total = progress_state["total"]
                if total > 0 and current != last:
                    last = current
                    percent = (current / total * 100)
                    bar = make_progress_bar(percent)
                    try:
                        await msg.edit_text(
                            f"📥 **دریافت فایل**\n\n"
                            f"`{bar}` `{percent:.1f}%`\n\n"
                            f"📏 `{format_bytes(current)}` / `{format_bytes(total)}`",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
                await asyncio.sleep(2)
        
        # شروع دانلود با Pyrogram
        progress_task = asyncio.create_task(update_progress())
        
        await download_from_telegram(message, temp_path, progress_callback)
        
        progress_state["done"] = True
        progress_state["current"] = file_size
        await asyncio.sleep(1)
        progress_task.cancel()
        
        if not temp_path.exists():
            raise Exception("دانلود فایل شکست خورد")
        
        actual_size = temp_path.stat().st_size
        
        await msg.edit_text(
            f"✅ **فایل دریافت شد!**\n\n"
            f"`■■■■■■■■■■■■■■■` `100%`\n\n"
            f"📁 `{safe_name}`\n"
            f"📏 `{format_bytes(actual_size)}`\n\n"
            f"💾 ذخیره در سرور",
            parse_mode="Markdown"
        )
        
        db.add_history(user_id, "upload", f"Telegram: {safe_name}", str(temp_path), actual_size)
        db.update_stats(user_id, "upload", actual_size)
        
    except Exception as e:
        error_msg = str(e)
        await msg.edit_text(f"❌ **خطا:**\n`{error_msg[:400]}`", parse_mode="Markdown")
    finally:
        # پاکسازی فایل موقت بعد از ۱ ساعت
        if temp_path and temp_path.exists():
            asyncio.create_task(cleanup_file(temp_path))

async def handle_caption_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""
    if "/up" in caption:
        update.message.reply_to_message = update.message
        await upload_command(update, context)

async def cleanup_file(file_path, delay=3600):
    await asyncio.sleep(delay)
    try:
        if file_path.exists():
            file_path.unlink()
    except:
        pass
