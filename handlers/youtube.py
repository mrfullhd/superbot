import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from core.youtube_dl import youtube_dl
from core.database import db
from utils.helpers import format_bytes

async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("📝 `/yt URL`", parse_mode="Markdown")
        return
    
    url = context.args[0]
    msg = await update.message.reply_text("⏳ در حال دانلود...")
    
    try:
        file_path, info = youtube_dl.download(url, user_id)
        size = format_bytes(file_path.stat().st_size)
        
        if file_path.stat().st_size < 50 * 1024 * 1024:
            await msg.edit_text(f"✅ دانلود شد!\n📁 `{file_path.name}`\n📏 `{size}`\n📤 در حال ارسال...", parse_mode="Markdown")
            await update.message.reply_video(
                video=open(file_path, "rb"),
                caption=f"✅ {size}",
                supports_streaming=True
            )
        else:
            await msg.edit_text(f"✅ دانلود شد!\n📁 `{file_path.name}`\n📏 `{size}`\n💾 ذخیره در سرور\n⚠️ فایل > 50MB", parse_mode="Markdown")
        
        db.add_history(user_id, "youtube", url, str(file_path), file_path.stat().st_size)
        db.update_stats(user_id, "youtube", file_path.stat().st_size)
        
    except Exception as e:
        err = str(e)
        if "Sign in" in err:
            await msg.edit_text("❌ نیاز به cookies\nفایل cookies.txt بفرستید + ریپلای `/cookie`", parse_mode="Markdown")
        else:
            await msg.edit_text(f"❌ `{err[:200]}`", parse_mode="Markdown")

async def mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("📝 `/mp3 URL`", parse_mode="Markdown")
        return
    
    url = context.args[0]
    msg = await update.message.reply_text("⏳ دانلود MP3...")
    
    try:
        file_path, info = youtube_dl.download(url, user_id, audio_only=True)
        size = format_bytes(file_path.stat().st_size)
        
        if file_path.stat().st_size < 50 * 1024 * 1024:
            await update.message.reply_audio(
                audio=open(file_path, "rb"),
                caption=f"✅ {size}",
                title=info.get("title", "MP3")
            )
        await msg.edit_text(f"✅ `{file_path.name}`\n📏 `{size}`", parse_mode="Markdown")
        
        db.add_history(user_id, "youtube_mp3", url, str(file_path), file_path.stat().st_size)
        db.update_stats(user_id, "youtube", file_path.stat().st_size)
        
    except Exception as e:
        await msg.edit_text(f"❌ `{str(e)[:200]}`", parse_mode="Markdown")
