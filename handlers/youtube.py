import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from core.youtube_dl import youtube_dl
from utils.helpers import format_bytes


# =====================================
# BUILD BUTTONS (ONLY SAFE FORMATS)
# =====================================
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


# =====================================
# /YT COMMAND
# =====================================
async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /yt url")
        return

    url = context.args[0]

    msg = await update.message.reply_text("⏳ Fetching formats...")

    try:
        data = youtube_dl.get_formats(url, user_id)

        keyboard = build_keyboard(data["formats"], url)

        await msg.edit_text(
            f"🎬 {data['title'][:80]}\n\nSelect quality:",
            reply_markup=keyboard
        )

    except Exception as e:
        await msg.edit_text(f"❌ Error:\n{str(e)[:300]}")


# =====================================
# CALLBACK DOWNLOAD
# =====================================
async def yt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, url, format_id = query.data.split("|")

        await query.edit_message_text("⬇️ Downloading...")

        file_path, info = youtube_dl.download(
            url=url,
            user_id=query.from_user.id,
            format_id=None if format_id == "best" else format_id
        )

        size = file_path.stat().st_size

        with open(file_path, "rb") as f:
            await query.message.reply_video(
                video=f,
                caption=f"🎬 {info.get('title','')}\n📦 {format_bytes(size)}",
                supports_streaming=True
            )

        await query.edit_message_text("✅ Done!")

    except Exception as e:
        await query.message.reply_text(f"❌ Error:\n{str(e)[:300]}")


# =====================================
# REGISTER CALLBACK
# =====================================
yt_callback_handler = CallbackQueryHandler(
    yt_callback,
    pattern="^yt\\|"
)
