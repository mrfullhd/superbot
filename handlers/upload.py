# handlers/upload.py

import time
import asyncio
from pathlib import Path
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from core.google_drive import get_drive_service
from core.database import db
from utils.helpers import format_bytes, sanitize_name, make_progress_bar

# Import Pyrogram
try:
    from pyrogram import Client
    import config
    pyro_app = Client(
        "azu_upload_session",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        no_updates=True
    )
    PYROGRAM_AVAILABLE = True
except Exception as e:
    print(f"Pyrogram not available: {e}")
    PYROGRAM_AVAILABLE = False

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آپلود فایل به Google Drive با Pyrogram (بدون محدودیت حجم)"""
    user_id = update.effective_user.id
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "📤 **آپلود فایل به Google Drive**\n\n"
            "1️⃣ یک فایل بفرستید\n"
            "2️⃣ روی آن ریپلای کنید\n"
            "3️⃣ `/up` را بفرستید\n\n"
            "💪 **فایل‌های با هر اندازه‌ای پشتیبانی می‌شن!**",
            parse_mode="Markdown"
        )
        return
    
    message = update.message.reply_to_message
    msg = await update.message.reply_text("📤 در حال آماده‌سازی آپلود...")
    
    temp_path = None
    
    try:
        # تشخیص نوع فایل
        file_id = None
        file_name = "unknown"
        file_size = 0
        
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name or "document"
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
        elif message.video_note:
            file_id = message.video_note.file_id
            file_name = f"videonote_{int(time.time())}.mp4"
            file_size = message.video_note.file_size
        elif message.sticker:
            file_id = message.sticker.file_id
            file_name = f"sticker_{int(time.time())}.webp"
            file_size = message.sticker.file_size
        else:
            await msg.edit_text("❌ نوع فایل پشتیبانی نمی‌شود")
            return
        
        safe_name = sanitize_name(file_name)
        temp_path = Path("downloads") / str(user_id) / safe_name
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ============================================
        # دانلود فایل از تلگرام
        # ============================================
        
        # روش ۱: Pyrogram (بدون محدودیت حجم) - برای همه فایل‌ها
        if PYROGRAM_AVAILABLE:
            await msg.edit_text(
                f"📥 **دریافت فایل با MTProto...**\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(file_size)}`\n\n"
                f"🔄 بدون محدودیت حجم",
                parse_mode="Markdown"
            )
            
            # شروع Pyrogram اگر لازم باشه
            if not pyro_app.is_connected:
                await pyro_app.start()
            
            # دریافت پیام با Pyrogram
            pyro_message = await pyro_app.get_messages(
                message.chat.id,
                message.message_id
            )
            
            # Progress callback برای Pyrogram
            last_update = [0]
            def pyro_progress(current, total):
                nonlocal last_update
                now = time.time()
                if now - last_update[0] >= 3:
                    last_update[0] = now
                    percent = (current / total * 100) if total > 0 else 0
                    bar = make_progress_bar(percent)
                    # آپدیت پیام در event loop
                    try:
                        asyncio.create_task(
                            msg.edit_text(
                                f"📥 **دریافت فایل...**\n\n"
                                f"`{bar}` `{percent:.1f}%`\n\n"
                                f"📏 `{format_bytes(current)}` / `{format_bytes(total)}`",
                                parse_mode="Markdown"
                            )
                        )
                    except:
                        pass
            
            # دانلود با Pyrogram
            await pyro_app.download_media(
                message=pyro_message,
                file_name=str(temp_path),
                progress=pyro_progress
            )
        
        # روش ۲: python-telegram-bot (فقط برای فایل‌های زیر 20MB)
        else:
            if file_size > 20 * 1024 * 1024:
                await msg.edit_text(
                    "❌ **فایل خیلی بزرگ است**\n\n"
                    f"📏 `{format_bytes(file_size)}`\n\n"
                    "🔧 برای پشتیبانی از فایل‌های بزرگ، Pyrogram نیاز است.\n"
                    "مطمئن شوید `Pyrogram` و `TgCrypto` نصب شده باشند.",
                    parse_mode="Markdown"
                )
                return
            
            await msg.edit_text(
                f"📥 **دریافت فایل...**\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(file_size)}`",
                parse_mode="Markdown"
            )
            
            file_obj = await context.bot.get_file(file_id)
            await file_obj.download_to_drive(str(temp_path))
        
        # ============================================
        # بررسی موفقیت دانلود
        # ============================================
        
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise Exception("دانلود فایل ناموفق بود")
        
        actual_size = temp_path.stat().st_size
        
        # ============================================
        # آپلود به Google Drive
        # ============================================
        
        drive = get_drive_service(user_id)
        drive_uploaded = False
        
        if drive:
            await msg.edit_text(
                f"📤 **آپلود به Google Drive...**\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(actual_size)}`",
                parse_mode="Markdown"
            )
            
            try:
                result = drive.upload_file(user_id, temp_path)
                drive_uploaded = True
            except Exception as e:
                print(f"Drive upload failed: {e}")
        
        # ============================================
        # پیام نهایی
        # ============================================
        
        if drive_uploaded:
            await msg.edit_text(
                f"✅ **آپلود کامل شد!**\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(actual_size)}`\n"
                f"💾 **Google Drive** ✅",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"✅ **فایل دریافت شد**\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(actual_size)}`\n\n"
                f"⚠️ برای آپلود خودکار به Drive، `/login` بزنید.",
                parse_mode="Markdown"
            )
        
        # ثبت در تاریخچه
        db.add_history(user_id, "upload", f"Telegram: {safe_name}", str(temp_path), actual_size)
        db.update_stats(user_id, "upload", actual_size)
        
    except Exception as e:
        error_msg = str(e)
        
        if "too large" in error_msg.lower() or "file is too big" in error_msg.lower():
            await msg.edit_text(
                "❌ **فایل خیلی بزرگ است**\n\n"
                "🔧 **راه حل:**\n"
                "1. فایل را مستقیماً در Google Drive آپلود کنید\n"
                "2. یا فایل را به بخش‌های کوچکتر تقسیم کنید",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ **خطا:**\n`{error_msg[:300]}`",
                parse_mode="Markdown"
            )
    
    finally:
        # پاکسازی فایل موقت
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass

async def handle_caption_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فایل با کپشن /up"""
    caption = update.message.caption or ""
    if "/up" in caption:
        # شبیه‌سازی ریپلای
        # پیام اصلی رو به عنوان reply_to_message ست می‌کنیم
        update.message.reply_to_message = update.message
        await upload_command(update, context)
