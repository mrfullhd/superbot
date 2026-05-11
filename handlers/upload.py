import time
import asyncio
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from core.google_drive import get_drive_service
from core.database import db
from utils.helpers import format_bytes, sanitize_name, make_progress_bar

# Pyrogram
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
    print(f"Pyrogram import error: {e}")
    PYROGRAM_AVAILABLE = False

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "📤 روی فایل ریپلای کنید و `/up` را بفرستید.\n"
            "💪 بدون محدودیت حجم با MTProto",
            parse_mode="Markdown"
        )
        return

    message = update.message.reply_to_message
    msg = await update.message.reply_text("📤 شروع فرآیند آپلود...")
    temp_path = None

    try:
        # 1. تشخیص فایل
        file_name = None
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
        elif message.voice:
            file_name = f"voice_{int(time.time())}.ogg"
            file_size = message.voice.file_size
        elif message.video_note:
            file_name = f"vn_{int(time.time())}.mp4"
            file_size = message.video_note.file_size
        elif message.sticker:
            file_name = f"sticker_{int(time.time())}.webp"
            file_size = message.sticker.file_size
        else:
            await msg.edit_text("❌ نوع فایل پشتیبانی نمی‌شود")
            return

        safe_name = sanitize_name(file_name)
        temp_path = Path("downloads") / str(user_id) / safe_name
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        # 2. دانلود با Pyrogram (MTProto)
        if not PYROGRAM_AVAILABLE:
            await msg.edit_text("❌ Pyrogram در دسترس نیست. فایل‌های بزرگ پشتیبانی نمی‌شوند.")
            return

        if not pyro_app.is_connected:
            await pyro_app.start()

        pyro_msg = await pyro_app.get_messages(message.chat.id, message.message_id)

        # Progress bar
        last_update = [0]
        def pyro_progress(current, total):
            now = time.time()
            if now - last_update[0] >= 2:
                last_update[0] = now
                percent = (current / total * 100) if total > 0 else 0
                bar = make_progress_bar(percent)
                asyncio.create_task(
                    msg.edit_text(
                        f"📥 دریافت فایل...\n{bar} {percent:.1f}%\n"
                        f"{format_bytes(current)} / {format_bytes(total)}",
                        parse_mode="Markdown"
                    )
                )

        await msg.edit_text("📥 در حال دریافت فایل از تلگرام...", parse_mode="Markdown")
        await pyro_app.download_media(
            message=pyro_msg,
            file_name=str(temp_path),
            progress=pyro_progress
        )

        if not temp_path.exists():
            raise Exception("دانلود فایل شکست خورد")

        final_size = temp_path.stat().st_size

        # 3. آپلود به Google Drive
        drive = get_drive_service(user_id)
        if drive:
            await msg.edit_text("📤 در حال آپلود به Google Drive...", parse_mode="Markdown")
            try:
                drive.upload_file(user_id, temp_path)
                await msg.edit_text(
                    f"✅ آپلود شد!\n📁 {safe_name}\n📏 {format_bytes(final_size)}\n💾 Google Drive",
                    parse_mode="Markdown"
                )
            except Exception as e:
                await msg.edit_text(f"❌ خطا در آپلود به Drive: {str(e)[:200]}", parse_mode="Markdown")
        else:
            await msg.edit_text(
                f"✅ فایل دریافت شد (در سرور)\n📁 {safe_name}\n📏 {format_bytes(final_size)}\n"
                "⚠️ برای آپلود خودکار /login بزنید.",
                parse_mode="Markdown"
            )

        # ثبت تاریخچه
        db.add_history(user_id, "upload", f"Telegram: {safe_name}", str(temp_path), final_size)
        db.update_stats(user_id, "upload", final_size)

    except Exception as e:
        error_msg = str(e)
        if "File too large" in error_msg or "too big" in error_msg:
            await msg.edit_text("❌ فایل بیش از حد بزرگ است. از روش جایگزین استفاده کنید.")
        else:
            await msg.edit_text(f"❌ خطا: {error_msg[:300]}", parse_mode="Markdown")
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass

async def handle_caption_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""
    if "/up" in caption:
        # شبیه‌سازی ریپلای به خودش
        update.message.reply_to_message = update.message
        await upload_command(update, context)
