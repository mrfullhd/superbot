from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from utils.helpers import format_bytes

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    user_stats = db.get_stats(user_id)
    total_stats = db.get_total_stats()
    
    if not user_stats:
        await update.message.reply_text("📊 هنوز آماری ثبت نشده.")
        return
    
    text = f"""
📊 **آمار شما:**

📥 کل دانلودها: `{user_stats['total_downloads']}`
📏 حجم کل: `{format_bytes(user_stats['total_size'])}`
🎬 یوتیوب: `{user_stats['youtube_downloads']}`
📄 مستقیم: `{user_stats['direct_downloads']}`
📤 آپلود: `{user_stats['uploads']}`

📈 **آمار کلی ربات:**

👥 کاربران: `{total_stats['total_users']}`
📥 کل دانلودها: `{total_stats['total_downloads']}`
📏 حجم کل: `{format_bytes(total_stats['total_size'])}`
"""
    
    await update.message.reply_text(text, parse_mode="Markdown")
