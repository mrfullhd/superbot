#!/usr/bin/env python3
# ============================================
# AzuDl Telegram Bot - Main Entry Point
# Python 3.11 + python-telegram-bot v20.7
# ============================================

import asyncio
import logging
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

# Import config
import config

# Import handlers
from handlers.start import start_command
from handlers.youtube import yt_command, mp3_command
from handlers.direct import direct_command
from handlers.upload import upload_command, handle_caption_upload
from handlers.cookies import cookie_command
from handlers.login import login_command, logout_command, code_command
from handlers.search import search_command
from handlers.playlist import playlist_command
from handlers.settings import settings_command, settings_callback
from handlers.stats import stats_command
from handlers.info import latest_command, files_command, history_command, storage_command
from handlers.formats import formats_command
from handlers.cancel import cancel_command, cancel_callback

# Import core
from core.database import db
from core.google_auth import google_auth

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# CREATE DIRECTORIES
# ============================================

def create_directories():
    """ساخت پوشه‌های مورد نیاز"""
    dirs = [
        "data/tokens",
        "downloads",
        "logs",
        "cookies"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

# ============================================
# BUILD APPLICATION
# ============================================

def build_application():
    """ساخت اپلیکیشن تلگرام"""
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # ============================================
    # COMMAND HANDLERS
    # ============================================
    
    # Basic commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    
    # Download commands
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
    
    # Settings
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("set", settings_command))
    
    # Stats
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("me", stats_command))
    
    # Info commands
    application.add_handler(CommandHandler("latest", latest_command))
    application.add_handler(CommandHandler("files", files_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("storage", storage_command))
    
    # Cancel
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # ============================================
    # MESSAGE HANDLERS
    # ============================================
    
    # Files with /up caption
    application.add_handler(
        MessageHandler(
            filters.CAPTION & filters.Regex(r'^/up'),
            handle_caption_upload
        )
    )
    
    # ============================================
    # CALLBACK QUERY HANDLERS
    # ============================================
    
    # Settings callback
    application.add_handler(
        CallbackQueryHandler(settings_callback, pattern="^(quality_|menu_settings$)")
    )
    
    # Cancel callback
    application.add_handler(
        CallbackQueryHandler(cancel_callback, pattern="^cancel_")
    )
    
    # Format selection callback
    application.add_handler(
        CallbackQueryHandler(formats_callback, pattern="^fmt_")
    )
    
    # Download selection from search
    application.add_handler(
        CallbackQueryHandler(download_callback, pattern="^dl_")
    )
    
    # Menu navigation
    application.add_handler(
        CallbackQueryHandler(menu_callback, pattern="^menu_")
    )
    
    return application

# ============================================
# CALLBACK HANDLERS
# ============================================

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی"""
    query = update.callback_query
    data = query.data
    
    if data == "menu_start":
        from handlers.start import start_command
        await query.message.delete()
        await start_command(update, context)
        return
    
    elif data == "menu_yt":
        await query.answer("🎬 لینک یوتیوب را با /yt بفرستید", show_alert=True)
    
    elif data == "menu_mp3":
        await query.answer("🎵 لینک را با /mp3 بفرستید", show_alert=True)
    
    elif data == "menu_search":
        await query.answer("🔍 از /search استفاده کنید", show_alert=True)
    
    elif data == "menu_login":
        await query.answer("🔐 در حال آماده‌سازی اتصال...")
        from handlers.login import login_command
        await login_command(update, context)
        return
    
    elif data == "menu_settings":
        from handlers.settings import settings_command
        await settings_command(update, context)
        return
    
    elif data == "menu_stats":
        from handlers.stats import stats_command
        await stats_command(update, context)
        return
    
    elif data == "menu_upload":
        await query.answer("📤 فایل بفرستید و /up را ریپلای کنید", show_alert=True)
    
    await query.answer()

async def formats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب فرمت برای دانلود"""
    query = update.callback_query
    data = query.data
    
    parts = data.split("_", 2)
    format_id = parts[1] if len(parts) > 1 else "best"
    url = context.user_data.get("format_url", "")
    
    if url:
        await query.answer(f"دانلود با فرمت {format_id} شروع شد...")
        context.user_data["selected_format"] = format_id
        context.args = [url]
        await query.message.delete()
        await yt_command(update, context)
    else:
        await query.answer("❌ لینک یافت نشد", show_alert=True)

async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دانلود از نتایج جستجو"""
    query = update.callback_query
    data = query.data
    
    video_id = data.replace("dl_", "")
    url = f"https://youtube.com/watch?v={video_id}"
    
    await query.answer("شروع دانلود...")
    context.args = [url]
    await query.message.delete()
    await yt_command(update, context)

# ============================================
# OAuth CALLBACK (For Web Server - Fallback)
# ============================================

async def oauth_callback(request):
    """
    هندلر callback از Google OAuth
    این تابع توسط وب‌سرور Flask صدا زده میشه
    """
    from urllib.parse import parse_qs, urlparse
    
    parsed = urlparse(request.url)
    params = parse_qs(parsed.query)
    
    code = params.get("code", [None])[0]
    state = params.get("state", [None])[0]
    
    if not code or not state:
        return "❌ Invalid request - missing code or state"
    
    user_id = int(state)
    success, result = google_auth.exchange_code(user_id, code, state)
    
    if success:
        return f"""
        <html dir="rtl">
        <head><meta charset="utf-8"></head>
        <body style="font-family: Tahoma, sans-serif; text-align: center; padding: 50px; background: #f0f8f0;">
            <h1 style="color: green;">✅ اتصال موفق!</h1>
            <p>Google Drive شما با موفقیت متصل شد.</p>
            <p>می‌توانید به ربات تلگرام برگردید.</p>
            <p style="color: gray;">ایمیل: {result}</p>
        </body>
        </html>
        """
    else:
        return f"""
        <html dir="rtl">
        <head><meta charset="utf-8"></head>
        <body style="font-family: Tahoma, sans-serif; text-align: center; padding: 50px; background: #fff0f0;">
            <h1 style="color: red;">❌ خطا در اتصال</h1>
            <p>{result}</p>
            <p style="color: gray;">لطفاً دوباره تلاش کنید یا از دستور /code استفاده کنید.</p>
        </body>
        </html>
        """

# ============================================
# WEB SERVER (For Runflare - Optional)
# ============================================

def create_web_app():
    """ساخت وب‌سرور برای OAuth callback"""
    try:
        from flask import Flask, request
        
        app = Flask(__name__)
        
        @app.route("/")
        def home():
            return "AzuDl Telegram Bot is running!"
        
        @app.route("/oauth2callback")
        def callback():
            import asyncio as aio
            loop = aio.new_event_loop()
            aio.set_event_loop(loop)
            result = loop.run_until_complete(oauth_callback(request))
            loop.close()
            return result
        
        return app
    except ImportError:
        logger.warning("Flask not installed - web server disabled")
        return None

# ============================================
# RUN
# ============================================

def main():
    """تابع اصلی اجرا"""
    
    # ساخت پوشه‌ها
    create_directories()
    
    # ساخت اپلیکیشن تلگرام
    application = build_application()
    
    logger.info("=" * 60)
    logger.info("AzuDl Telegram Bot Starting...")
    logger.info(f"Bot: {config.BOT_USERNAME}")
    logger.info("=" * 60)
    
    # اجرای وب‌سرور در thread جدا (اختیاری)
    web_app = create_web_app()
    if web_app:
        import threading
        web_thread = threading.Thread(
            target=web_app.run,
            kwargs={
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False,
                "use_reloader": False
            },
            daemon=True
        )
        web_thread.start()
        logger.info("🌐 Web server started on port 8080 (for OAuth callback)")
    else:
        logger.info("ℹ️ Web server disabled - use /code command for OAuth")
    
    # اجرای ربات تلگرام
    logger.info("🤖 Starting Telegram bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
