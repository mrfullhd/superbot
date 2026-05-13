from telegram import Update
from telegram.ext import ContextTypes

from core.google_drive import get_drive_service
from core.database import db
from core.uploader import download_from_telegram

from utils.helpers import format_bytes, sanitize_name

from pathlib import Path
import time


# =========================================
# /up COMMAND (FIXED MTProto)
# =========================================
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not update.message.reply_to_message:
        await update.message.reply_text("📤 روی فایل ریپلای کنید + /up")
        return

    message = update.message.reply_to_message

    # =====================================
    # DETECT FILE
    # =====================================
    if message.document:
        file_name = message.document.file_name or "file"
    elif message.video:
        file_name = message.video.file_name or f"video_{int(time.time())}.mp4"
    elif message.audio:
        file_name = message.audio.file_name or f"audio_{int(time.time())}.mp3"
    elif message.photo:
        file_name = f"photo_{int(time.time())}.jpg"
    elif message.voice:
        file_name = f"voice_{int(time.time())}.ogg"
    else:
        await update.message.reply_text("❌ نوع فایل پشتیبانی نمی‌شود")
        return

    msg = await update.message.reply_text("⬇️ Downloading via MTProto...")

    try:
        # =====================================
        # SAFE PATH
        # =====================================
        safe_name = sanitize_name(file_name)
        temp_path = Path("downloads") / str(user_id) / safe_name
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        # =====================================
        # 🚀 PYROGRAM DOWNLOAD (NO LIMIT FIX)
        # =====================================
        await download_from_telegram(
            message,
            temp_path
        )

        file_size = temp_path.stat().st_size

        await msg.edit_text("📤 Uploading to Google Drive...")

        # =====================================
        # DRIVE UPLOAD
        # =====================================
        drive = get_drive_service(user_id)
        drive_uploaded = False

        if drive:
            try:
                drive.upload_file(user_id, temp_path)
                drive_uploaded = True
            except Exception as e:
                print("Drive error:", e)

        # =====================================
        # RESULT
        # =====================================
        text = (
            f"✅ Upload Done!\n\n"
            f"📁 {safe_name}\n"
            f"📦 {format_bytes(file_size)}\n"
        )

        if drive_uploaded:
            text += "💾 Google Drive\n"

        await msg.edit_text(text)

        # DB
        db.add_history(user_id, "upload", safe_name, str(temp_path), file_size)
        db.update_stats(user_id, "upload", file_size)

        # cleanup
        try:
            temp_path.unlink()
        except:
            pass

    except Exception as e:
        await msg.edit_text(f"❌ Error:\n{str(e)[:300]}")


# =========================================
# /up caption handler
# =========================================
async def handle_caption_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "/up" in (update.message.caption or ""):
        await upload_command(update, context)
