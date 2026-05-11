from telegram import Update
from telegram.ext import ContextTypes
from core.youtube_dl import youtube_dl
from keyboards.inline import formats_keyboard

async def formats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("📝 `/formats URL`", parse_mode="Markdown")
        return
    
    url = context.args[0]
    msg = await update.message.reply_text("🔍 دریافت فرمت‌ها...")
    
    try:
        info = youtube_dl.get_formats(url, user_id)
        
        context.user_data["format_url"] = url
        
        text = f"📹 **{info['title'][:100]}**\n\n"
        text += "فرمت‌های موجود:\n"
        
        for fmt in info['formats'][:10]:
            size_str = format_bytes_s(fmt['filesize']) if fmt.get('filesize') else "نامشخص"
            text += f"- {fmt['resolution']} ({fmt['ext']}) - {size_str}\n"
        
        await msg.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=formats_keyboard(info['formats'], url)
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ `{str(e)[:200]}`", parse_mode="Markdown")

def format_bytes_s(size):
    if not size:
        return "نامشخص"
    return format_bytes(size)

from utils.helpers import format_bytes
