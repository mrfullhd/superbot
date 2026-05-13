#!/usr/bin/env python3
# ============================================
# AzuDl Telegram Bot - Main Entry Point
# Python 3.11 + python-telegram-bot v20.7
# ============================================

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

import config

# ============================================
# HANDLERS IMPORT
# ============================================

from handlers.start import start_command
from handlers.youtube import yt_command, mp3_command, yt_callback
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

# core
from core.database import db
from core.google_auth import google_auth

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================
# DIRECTORIES
# ============================================

def create_directories():
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
    application = Application.builder().token(config.BOT_TOKEN).build()

    # ========================================
    # COMMAND HANDLERS
    # ========================================

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))

    # YouTube system (NEW)
    application.add_handler(CommandHandler("yt", yt_command))
    application.add_handler(CommandHandler("mp3", mp3_command))
    application.add_handler(CommandHandler("dl", yt_command))

    # Other download
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

    # Login system
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

    # Info
    application.add_handler(CommandHandler("latest", latest_command))
    application.add_handler(CommandHandler("files", files_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("storage", storage_command))

    # Cancel
    application.add_handler(CommandHandler("cancel", cancel_command))

    # ========================================
    # MESSAGE HANDLERS
    # ========================================

    application.add_handler(
        MessageHandler(
            filters.CAPTION & filters.Regex(r'^/up'),
            handle_caption_upload
        )
    )

    # ========================================
    # CALLBACK HANDLERS
    # ========================================

    # settings
    application.add_handler(
        CallbackQueryHandler(settings_callback, pattern="^(quality_|menu_settings$)")
    )

    # cancel
    application.add_handler(
        CallbackQueryHandler(cancel_callback, pattern="^cancel_")
    )

    # ================================
    # NEW YOUTUBE CALLBACK (IMPORTANT)
    # ================================
    application.add_handler(
        CallbackQueryHandler(yt_callback, pattern="^yt\\|")
    )

    # menu navigation
    application.add_handler(
        CallbackQueryHandler(menu_callback, pattern="^menu_")
    )

    return application


# ============================================
# MENU CALLBACK
# ============================================

async def menu_callback(update: Update, context):
    query = update.callback_query
    data = query.data

    if data == "menu_start":
        await query.message.delete()
        await start_command(update, context)

    elif data == "menu_yt":
        await query.answer("🎬 /yt URL ارسال کنید", show_alert=True)

    elif data == "menu_mp3":
        await query.answer("🎵 /mp3 URL ارسال کنید", show_alert=True)

    elif data == "menu_search":
        await query.answer("🔍 /search استفاده کنید", show_alert=True)

    elif data == "menu_login":
        await query.answer("🔐 در حال آماده‌سازی...")
        await login_command(update, context)

    elif data == "menu_settings":
        await settings_command(update, context)

    elif data == "menu_stats":
        await stats_command(update, context)

    elif data == "menu_upload":
        await query.answer("📤 فایل + /up", show_alert=True)

    await query.answer()


# ============================================
# OAUTH CALLBACK
# ============================================

async def oauth_callback(request):
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(request.url)
    params = parse_qs(parsed.query)

    code = params.get("code", [None])[0]
    state = params.get("state", [None])[0]

    if not code or not state:
        return "Invalid request"

    user_id = int(state)
    success, result = google_auth.exchange_code(user_id, code, state)

    if success:
        return "<h1>OK Connected</h1>"
    else:
        return f"<h1>Error</h1><p>{result}</p>"


# ============================================
# WEB SERVER (OPTIONAL)
# ============================================

def create_web_app():
    try:
        from flask import Flask, request

        app = Flask(__name__)

        @app.route("/")
        def home():
            return "AzuDl Bot Running"

        @app.route("/oauth2callback")
        def callback():
            import asyncio as aio
            loop = aio.new_event_loop()
            aio.set_event_loop(loop)
            return loop.run_until_complete(oauth_callback(request))

        return app

    except ImportError:
        logger.warning("Flask not installed")
        return None


# ============================================
# MAIN
# ============================================

def main():
    create_directories()

    application = build_application()

    logger.info("=" * 50)
    logger.info("AzuDl Bot Starting...")
    logger.info(f"Bot: {config.BOT_USERNAME}")
    logger.info("=" * 50)

    # optional web server
    web_app = create_web_app()
    if web_app:
        import threading

        thread = threading.Thread(
            target=web_app.run,
            kwargs={
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False
            },
            daemon=True
        )
        thread.start()

        logger.info("Web server started on port 8080")

    # run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
