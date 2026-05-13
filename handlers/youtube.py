import asyncio
import time
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from core.youtube_dl import youtube_dl
from core.google_drive import get_drive_service
from core.downloader import download_manager
from core.database import db
from utils.helpers import format_bytes, make_progress_bar
from keyboards.inline import cancel_keyboard


# ============================================
# KEYBOARD BUILDER (INLINE QUALITY SELECTOR)
# ============================================

def build_keyboard(formats, url):
    buttons = []

    for f in formats:
        label = ""

        # video + audio
        if f.get("vcodec") != "none" and f.get("acodec") != "none":
            label = f"🎬 {f.get('resolution','?')}p {f.get('ext','')}"
        # audio only
        elif f.get("vcodec") == "none":
            label = f"🎵 Audio {f.get('ext','')}"
        else:
            label = f"🎥 {f.get('resolution','?')}p"

        buttons.append([
            InlineKeyboardButton(
                label,
                callback_data=f"yt|{url}|{f['format_id']}"
            )
        ])

    # best quality button
    buttons.append([
        InlineKeyboardButton(
            "⚡ Best Quality",
            callback_data=f"yt|{url}|best"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# ============================================
# /YT COMMAND (STEP 1: SHOW FORMATS)
# ============================================

async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "📝 **نحوه استفاده:**\n`/yt URL`",
            parse_mode="Markdown"
        )
        return

    url = context.args[0]

    msg = await update.message.reply_text("⏳ در حال بررسی کیفیت‌ها...")

    try:
        data = youtube_dl.get_formats(url, user_id)

        keyboard = build_keyboard(data["formats"], url)

        await msg.edit_text(
            f"🎬 **{data['title'][:80]}**\n\n👇 کیفیت مورد نظر را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دریافت اطلاعات:\n`{str(e)[:300]}`", parse_mode="Markdown")


# ============================================
# CALLBACK HANDLER (STEP 2: DOWNLOAD SELECTED FORMAT)
# ============================================

async def yt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, url, format_id = query.data.split("|")

        await query.edit_message_text("⬇️ در حال دانلود...")

        file_path, info = youtube_dl.download(
            url=url,
            user_id=query.from_user.id,
            format_id=None if format_id == "best" else format_id
        )

        file_size = file_path.stat().st_size

        # Telegram send
        await query.message.reply_video(
            video=open(file_path, "rb"),
            caption=(
                f"🎬 {info.get('title','Unknown')[:100]}\n"
                f"📏 {format_bytes(file_size)}"
            ),
            supports_streaming=True
        )

        # history save
        db.add_history(
            query.from_user.id,
            "youtube",
            url,
            str(file_path),
            file_size
        )

        db.update_stats(query.from_user.id, "youtube", file_size)

    except Exception as e:
        await query.message.reply_text(
            f"❌ خطا در دانلود:\n`{str(e)[:300]}`",
            parse_mode="Markdown"
        )


# ============================================
# MP3 COMMAND (UNCHANGED - OPTIONAL)
# ============================================

async def mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /mp3 URL")
        return

    url = context.args[0]
    download_id = download_manager.add_download(user_id, url, "YouTube MP3")

    msg = await update.message.reply_text("⏳ در حال دانلود MP3...")

    file_path = None

    try:
        download_manager.start_download(download_id)

        file_path, info = youtube_dl.download(
            url,
            user_id,
            audio_only=True
        )

        if download_manager.is_cancelled(download_id):
            await msg.edit_text("🚫 لغو شد")
            return

        file_size = file_path.stat().st_size

        drive = get_drive_service(user_id)
        drive_uploaded = False

        if drive:
            try:
                drive.upload_file(user_id, file_path)
                drive_uploaded = True
            except Exception as e:
                print(e)

        if file_size < 50 * 1024 * 1024:
            await update.message.reply_audio(
                audio=open(file_path, "rb"),
                caption=f"🎵 {info.get('title','')[:100]}",
                title=info.get('title','Unknown'),
                duration=info.get('duration', 0)
            )

    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n`{str(e)[:300]}`")

    finally:
        download_manager.finish_download(download_id)


# ============================================
# CLEANUP
# ============================================

async def cleanup_file(file_path, delay=3600):
    await asyncio.sleep(delay)
    try:
        if file_path and file_path.exists():
            file_path.unlink()
    except Exception:
        pass


# ============================================
# REGISTER CALLBACK HANDLER (IMPORTANT)
# ============================================

yt_callback_handler = CallbackQueryHandler(
    yt_callback,
    pattern="^yt\\|"
)
