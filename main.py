#!/usr/bin/env python3
# ============================================
# AzuDl Telegram Bot - Complete Version
# همه قابلیت‌ها: یوتیوب + دایرکت + آپلود + گوگل درایو + کوکی
# ============================================

import asyncio
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

import config
from core.database import db

# Import all handlers
from handlers.youtube import yt_command, mp3_command
from handlers.direct import direct_command
from handlers.upload import upload_command, handle_caption_upload
from handlers.cookies import cookie_command
from handlers.login import login_command, logout_command, code_command
from handlers.search import search_command
from handlers.playlist import playlist_command
from handlers.formats import formats_command
from handlers.cancel import cancel_command
from handlers.info import (
    files_command,
    history_command,
    storage_command,
    latest_command,
    stats_command
)

# ============================================
# CREATE DIRECTORIES
# ============================================

def create_directories():
    dirs = ["downloads", "logs", "cookies"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

# ============================================
# START COMMAND
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.add_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    text = """
🤖 **AzuDl Telegram Bot**

📥 **دانلود:**
`/yt URL` - دانلود ویدیو یوتیوب
`/mp3 URL` - دانلود صدا از یوتیوب
`/direct URL` - دانلود مستقیم فایل
`/formats URL` - نمایش کیفیت‌های موجود

🔍 **جستجو:**
`/search متن` - جستجوی ویدیو در یوتیوب
`/playlist URL` - اطلاعات playlist

📤 **آپلود:**
`/up` - آپلود فایل به سرور (روی فایل ریپلای کنید)
💪 **بدون محدودیت حجم** با MTProto

🔐 **Google Drive:**
`/login` - اتصال به Google Drive
`/logout` - قطع اتصال
`/code` - تکمیل احراز هویت با کد

🍪 **Cookies:**
`/cookie` - ذخیره cookies.txt برای یوتیوب

📊 **مدیریت:**
`/files` - لیست فایل‌ها
`/latest` - آخرین فایل
`/history` - تاریخچه
`/storage` - فضای دیسک
`/stats` - آمار دانلودها
`/cancel` - لغو دانلود
"""
    await update.message.reply_text(text, parse_mode="Markdown")

# ============================================
# BUILD APPLICATION
# ============================================

def build_application():
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Basic
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    
    # Download
    application.add_handler(CommandHandler("yt", yt_command))
    application.add_handler(CommandHandler("mp3", mp3_command))
    application.add_handler(CommandHandler("dl", yt_command))
    application.add_handler(CommandHandler("direct", direct_command))
    application.add_handler(CommandHandler("formats", formats_command))
    
    # Upload
    application.add_handler(CommandHandler("up", upload_command))
    
    # Search
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("s", search_command))
    
    # Playlist
    application.add_handler(CommandHandler("playlist", playlist_command))
    application.add_handler(CommandHandler("pl", playlist_command))
    
    # Google Drive OAuth
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(CommandHandler("code", code_command))
    
    # Cookies
    application.add_handler(CommandHandler("cookie", cookie_command))
    
    # Info
    application.add_handler(CommandHandler("files", files_command))
    application.add_handler(CommandHandler("latest", latest_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("storage", storage_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("me", stats_command))
    
    # Cancel
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Message handler for /up caption
    application.add_handler(
        MessageHandler(
            filters.CAPTION & filters.Regex(r'^/up'),
            handle_caption_upload
        )
    )
    
    return application

# ============================================
# MAIN
# ============================================

def main():
    create_directories()
    application = build_application()
    
    print("=" * 60)
    print("✅ AzuDl Bot - Complete Version")
    print("All features: YouTube + Direct + Upload + Google Drive + Cookies")
    print("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
