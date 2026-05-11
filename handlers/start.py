from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from keyboards.inline import main_menu

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)
    
    text = f"""
👋 سلام {user.first_name}!

🤖 **AzuDl Bot** - ربات دانلود و آپلود

📥 دانلود از یوتیوب و لینک مستقیم
📤 آپلود فایل به Google Drive شخصی
🔍 جستجوی ویدیو در یوتیوب
🎵 تبدیل ویدیو به MP3
🍪 پشتیبانی از cookies

از منوی زیر استفاده کنید یا دستورات را بفرستید:
"""
    await update.message.reply_text(text, reply_markup=main_menu())
