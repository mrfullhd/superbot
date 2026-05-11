from telegram import Update
from telegram.ext import ContextTypes
from core.database import db

async def cookie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.reply_to_message and update.message.reply_to_message.document:
        msg = await update.message.reply_text("🍪 ذخیره cookies...")
        
        try:
            file_id = update.message.reply_to_message.document.file_id
            file_obj = await context.bot.get_file(file_id)
            cookies_bytes = await file_obj.download_as_bytearray()
            cookies_text = bytes(cookies_bytes).decode('utf-8')
            
            db.save_cookies(user_id, cookies_text)
            
            await msg.edit_text("✅ Cookies ذخیره شد! حالا می‌تونید از یوتیوب دانلود کنید.")
            
        except Exception as e:
            await msg.edit_text(f"❌ `{str(e)[:200]}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "🍪 فایل cookies.txt را بفرستید\n"
            "سپس روی آن ریپلای کنید و `/cookie` بزنید.",
            parse_mode="Markdown"
        )
