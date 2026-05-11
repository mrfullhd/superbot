from telegram import Update
from telegram.ext import ContextTypes
from core.youtube_dl import youtube_dl

async def playlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("📝 `/playlist URL`", parse_mode="Markdown")
        return
    
    url = context.args[0]
    msg = await update.message.reply_text("📋 دریافت اطلاعات playlist...")
    
    try:
        info = youtube_dl.get_playlist_info(url, user_id)
        
        text = f"📋 **{info['title']}**\n\n"
        text += f"📊 تعداد ویدیوها: {info['count']}\n\n"
        
        for i, entry in enumerate(info['entries'][:15], 1):
            text += f"{i}. {entry['title'][:50]}\n"
        
        if info['count'] > 15:
            text += f"\n... و {info['count'] - 15} ویدیو دیگر"
        
        text += f"\n\nبرای دانلود کل playlist از دستور زیر استفاده کنید:"
        text += f"\n`/yt {url}`"
        
        await msg.edit_text(text, parse_mode="Markdown")
        
    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n`{str(e)[:200]}`", parse_mode="Markdown")
