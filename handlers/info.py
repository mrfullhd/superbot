# handlers/info.py

import shutil
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from utils.helpers import format_bytes
import config

async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست فایل‌های دانلود شده"""
    user_id = update.effective_user.id
    user_dir = Path(config.DOWNLOAD_PATH) / str(user_id)
    
    if not user_dir.exists():
        await update.message.reply_text("📭 هیچ فایلی دانلود نشده.")
        return
    
    files = []
    for f in user_dir.glob("**/*"):
        if f.is_file():
            files.append(f)
    
    if not files:
        await update.message.reply_text("📭 هیچ فایلی یافت نشد.")
        return
    
    files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:20]
    
    text = ["📂 **فایل‌های دانلود شده:**\n"]
    for f in files:
        size = format_bytes(f.stat().st_size)
        text.append(f"📄 `{size}` - {f.name[:50]}")
    
    text.append(f"\n📊 **مجموع:** {len(files)} فایل")
    
    await update.message.reply_text("\n".join(text), parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه دانلودها"""
    user_id = update.effective_user.id
    history = db.get_history(user_id, 10)
    
    if not history:
        await update.message.reply_text("📭 تاریخچه خالی است.")
        return
    
    text = ["📋 **۱۰ فعالیت آخر:**\n"]
    for item in history:
        type_emoji = {
            "youtube": "🎬",
            "youtube_mp3": "🎵",
            "direct": "📥",
            "upload": "📤"
        }.get(item.get("type", ""), "📄")
        
        date = item.get("date", "")
        if hasattr(date, 'strftime'):
            date = date.strftime("%Y-%m-%d %H:%M")
        
        text.append(f"{type_emoji} {item.get('type', '?')} - {date}")
    
    await update.message.reply_text("\n".join(text), parse_mode="Markdown")


async def storage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش فضای دیسک سرور"""
    total, used, free = shutil.disk_usage("/")
    
    percent = (used / total) * 100
    bar_length = 15
    filled = int(percent / 100 * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    text = (
        f"💾 **فضای سرور**\n\n"
        f"`{format_bytes(used)}` / `{format_bytes(total)}`\n"
        f"[{bar}] {percent:.1f}%\n\n"
        f"🟢 آزاد: `{format_bytes(free)}`"
    )
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آخرین فایل دانلود شده"""
    user_id = update.effective_user.id
    user_dir = Path(config.DOWNLOAD_PATH) / str(user_id)
    
    if not user_dir.exists():
        await update.message.reply_text("📭 فایلی نیست.")
        return
    
    files = [f for f in user_dir.glob("**/*") if f.is_file()]
    if not files:
        await update.message.reply_text("📭 فایلی نیست.")
        return
    
    latest = max(files, key=lambda x: x.stat().st_mtime)
    size = format_bytes(latest.stat().st_size)
    
    await update.message.reply_text(
        f"📁 **آخرین فایل**\n\n"
        f"📄 `{latest.name}`\n"
        f"📏 `{size}`",
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار دانلودهای کاربر"""
    user_id = update.effective_user.id
    
    user_stats = db.get_stats(user_id)
    total_stats = db.get_total_stats()
    
    if not user_stats:
        await update.message.reply_text("📊 هنوز آماری ثبت نشده.")
        return
    
    text = f"""
📊 **آمار شما:**

📥 کل دانلودها: `{user_stats.get('total_downloads', 0)}`
📏 حجم کل: `{format_bytes(user_stats.get('total_size', 0))}`
🎬 یوتیوب: `{user_stats.get('youtube_downloads', 0)}`
📄 مستقیم: `{user_stats.get('direct_downloads', 0)}`
📤 آپلود: `{user_stats.get('uploads', 0)}`

📈 **آمار کلی ربات:**

👥 کاربران: `{total_stats.get('total_users', 0)}`
📥 کل دانلودها: `{total_stats.get('total_downloads', 0)}`
📏 حجم کل: `{format_bytes(total_stats.get('total_size', 0))}`
"""
    
    await update.message.reply_text(text, parse_mode="Markdown")
