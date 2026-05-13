import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from core.youtube_dl import youtube_dl
from core.database import db
from utils.helpers import format_bytes
from core.google_drive import get_drive_service
from core.downloader import download_manager
from keyboards.inline import cancel_keyboard


# ============================================
# BUILD INLINE KEYBOARD (FORMATS)
# ============================================
def build_keyboard(formats, url):
    buttons = []

    for f in formats:
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")

        if vcodec != "none" and acodec != "none":
            label = f"🎬 {f.get('resolution','?')}p"
        elif vcodec == "none":
            label = "🎵 Audio"
        else:
            label = f"🎥 {f.get('resolution','?')}p"

        buttons.append([
            InlineKeyboardButton(
                label,
                callback_data=f"yt|{url}|{f['format_id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("⚡ Best Quality", callback_data=f"yt|{url}|best")
    ])

    return InlineKeyboardMarkup(buttons)


# ============================================
# /YT COMMAND
# ============================================
async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "📝 Usage:\n/yt url"
        )
        return

    url = context.args[0]

    msg = await update.message.reply_text("⏳ Getting video info...")

    try:
        data = youtube_dl.get_formats(url, user_id)

        keyboard = build_keyboard(data["formats"], url)

        await msg.edit_text(
            f"🎬 {data['title'][:80]}\n\n👇 Select quality:",
            reply_markup=keyboard
        )

    except Exception as e:
        await msg.edit_text(f"❌ Error:\n{str(e)[:300]}")


# ============================================
# CALLBACK HANDLER (DOWNLOAD SELECTED FORMAT)
# ============================================
async def yt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    try:
        _, url, format_id = query.data.split("|")

        await query.edit_message_text("⬇️ Downloading...")

        download_manager.add_download(user_id, url, "YouTube")
        download_manager.start_download(user_id)

        file_path, info = youtube_dl.download(
            url=url,
            user_id=user_id,
            format_id=None if format_id == "best" else format_id
        )

        if download_manager.is_cancelled(user_id):
            await query.edit_message_text("🚫 Cancelled")
            return

        size = file_path.stat().st_size

        # upload to drive (optional)
        drive_uploaded = False
        drive = get_drive_service(user_id)

        if drive:
            try:
                drive.upload_file(user_id, file_path)
                drive_uploaded = True
            except Exception:
                pass

        # send to telegram
        with open(file_path, "rb") as f:
            await query.message.reply_video(
                video=f,
                caption=(
                    f"🎬 {info.get('title','Unknown')[:100]}\n"
                    f"📦 {format_bytes(size)}"
                    f"{' | 💾 Drive' if drive_uploaded else ''}"
                ),
                supports_streaming=True
            )

        db.add_history(user_id, "youtube", url, str(file_path), size)
        db.update_stats(user_id, "youtube", size)

        await query.edit_message_text("✅ Done!")

    except Exception as e:
        await query.message.reply_text(
            f"❌ Download error:\n{str(e)[:300]}"
        )


# ============================================
# MP3 COMMAND (OPTIONAL BUT CLEANED)
# ============================================
async def mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /mp3 url")
        return

    url = context.args[0]

    msg = await update.message.reply_text("⏳ Downloading audio...")

    try:
        file_path, info = youtube_dl.download(
            url=url,
            user_id=user_id,
            audio_only=True
        )

        size = file_path.stat().st_size

        with open(file_path, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption=f"🎵 {info.get('title','')[:100]}\n📦 {format_bytes(size)}",
                title=info.get("title", "Unknown"),
                duration=info.get("duration", 0)
            )

        db.add_history(user_id, "youtube_mp3", url, str(file_path), size)
        db.update_stats(user_id, "youtube", size)

        await msg.edit_text("✅ Done!")

    except Exception as e:
        await msg.edit_text(f"❌ Error:\n{str(e)[:300]}")


# ============================================
# REGISTER CALLBACK
# ============================================
yt_callback_handler = CallbackQueryHandler(
    yt_callback,
    pattern="^yt\\|"
)
