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

# ThreadPoolExecutor برای آپلود blocking
import concurrent.futures
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آپلود فایل به Google Drive با Pyrogram + Progress Bar"""
    user_id = update.effective_user.id

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "📤 **آپلود فایل به Google Drive**\n\n"
            "1️⃣ یک فایل بفرستید\n"
            "2️⃣ روی آن ریپلای کنید\n"
            "3️⃣ `/up` را بفرستید\n\n"
            "💪 **بدون محدودیت حجم با MTProto**",
            parse_mode="Markdown"
        )
        return

    message = update.message.reply_to_message
    msg = await update.message.reply_text("📤 **شروع آپلود...**", parse_mode="Markdown")

    temp_path = None

    try:
        # ============================================
        # مرحله ۱: تشخیص فایل
        # ============================================
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
        elif message.voice:
            file_name = f"voice_{int(time.time())}.ogg"
            file_size = message.voice.file_size
        elif message.video_note:
            file_name = f"videonote_{int(time.time())}.mp4"
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

        # ============================================
        # مرحله ۲: دانلود با Pyrogram + Progress Bar
        # ============================================

        if not PYROGRAM_AVAILABLE:
            await msg.edit_text("❌ Pyrogram در دسترس نیست")
            return

        if not pyro_app.is_connected:
            await pyro_app.start()

        # دریافت پیام با Pyrogram
        pyro_msg = await pyro_app.get_messages(message.chat.id, message.message_id)

        # Progress state
        download_state = {"current": 0, "total": file_size, "done": False}

        def pyro_progress(current, total):
            download_state["current"] = current
            download_state["total"] = total

        # آپدیت کننده progress
        async def show_download_progress():
            last = 0
            while not download_state["done"]:
                current = download_state["current"]
                total = download_state["total"]
                if total > 0 and current != last:
                    last = current
                    percent = (current / total * 100)
                    bar = make_progress_bar(percent)
                    text = (
                        f"📥 **دریافت از تلگرام**\n\n"
                        f"`{bar}` `{percent:.1f}%`\n\n"
                        f"📏 `{format_bytes(current)}` / `{format_bytes(total)}`"
                    )
                    try:
                        await msg.edit_text(text, parse_mode="Markdown")
                    except:
                        pass
                await asyncio.sleep(2)

        # شروع همزمان دانلود و progress
        progress_task = asyncio.create_task(show_download_progress())

        await pyro_app.download_media(
            message=pyro_msg,
            file_name=str(temp_path),
            progress=pyro_progress
        )

        # پایان دانلود
        download_state["done"] = True
        download_state["current"] = file_size
        await asyncio.sleep(1)
        progress_task.cancel()

        if not temp_path.exists():
            raise Exception("دانلود فایل شکست خورد")

        actual_size = temp_path.stat().st_size

        # ============================================
        # مرحله ۳: آپلود به Drive + Progress Bar
        # ============================================

        drive = get_drive_service(user_id)

        if drive:
            await msg.edit_text(
                f"📥 **دریافت کامل**\n\n"
                f"`■■■■■■■■■■■■■■■` `100%`\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(actual_size)}`\n\n"
                f"📤 **در حال آپلود به Drive...**",
                parse_mode="Markdown"
            )

            # Progress برای آپلود
            upload_state = {"current": 0, "total": actual_size, "done": False}

            def drive_progress(current, total):
                upload_state["current"] = current
                upload_state["total"] = total

            async def show_upload_progress():
                start_time = time.time()
                while not upload_state["done"]:
                    current = upload_state["current"]
                    total = upload_state["total"]
                    if total > 0 and current > 0:
                        percent = (current / total * 100)
                        bar = make_progress_bar(percent)
                        elapsed = time.time() - start_time
                        speed = current / elapsed if elapsed > 0 else 0
                        eta = (total - current) / speed if speed > 0 else 0
                        text = (
                            f"📤 **آپلود به Google Drive**\n\n"
                            f"`{bar}` `{percent:.1f}%`\n\n"
                            f"📏 `{format_bytes(current)}` / `{format_bytes(total)}`\n"
                            f"⚡ `{format_bytes(speed)}/s` | ⏳ `{int(eta)}s`"
                        )
                        try:
                            await msg.edit_text(text, parse_mode="Markdown")
                        except:
                            pass
                    await asyncio.sleep(2)

            upload_task = asyncio.create_task(show_upload_progress())

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                drive.upload_file,
                user_id,
                temp_path,
                drive_progress
            )

            upload_state["done"] = True
            upload_state["current"] = actual_size
            await asyncio.sleep(1)
            upload_task.cancel()

            await msg.edit_text(
                f"✅ **آپلود کامل شد!**\n\n"
                f"`■■■■■■■■■■■■■■■` `100%`\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(actual_size)}`\n"
                f"💾 **Google Drive**",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"✅ **فایل دریافت شد!**\n\n"
                f"📁 `{safe_name}`\n"
                f"📏 `{format_bytes(actual_size)}`\n\n"
                f"⚠️ برای آپلود خودکار، `/login` بزنید.",
                parse_mode="Markdown"
            )

        # ثبت در تاریخچه
        db.add_history(user_id, "upload", f"Telegram: {safe_name}", str(temp_path), actual_size)
        db.update_stats(user_id, "upload", actual_size)

    except Exception as e:
        error_msg = str(e)
        if "too large" in error_msg.lower() or "file is too big" in error_msg.lower():
            await msg.edit_text(
                f"❌ **فایل خیلی بزرگ است**\n\n"
                f"📏 `{format_bytes(file_size)}`\n\n"
                f"🔧 فایل را مستقیماً در Google Drive آپلود کنید",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(f"❌ **خطا:**\n`{error_msg[:400]}`", parse_mode="Markdown")

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
        # شبیه‌سازی ریپلای به خودش
        update.message.reply_to_message = update.message
        await upload_command(update, context)
