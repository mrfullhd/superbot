# handlers/youtube.py

import asyncio
import time
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from core.youtube_dl import youtube_dl
from core.google_drive import get_drive_service
from core.downloader import download_manager
from core.database import db
from utils.helpers import format_bytes, make_progress_bar
from keyboards.inline import cancel_keyboard

# ============================================
# دانلود ویدیو از یوتیوب
# ============================================

async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "📝 **نحوه استفاده:**\n`/yt URL`\n\n"
            "مثال:\n`/yt https://youtube.com/watch?v=...`",
            parse_mode="Markdown"
        )
        return
    
    url = context.args[0]
    download_id = download_manager.add_download(user_id, url, "YouTube Video")
    
    msg = await update.message.reply_text(
        "⏳ **در حال دریافت اطلاعات ویدیو...**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(download_id)
    )
    
    file_path = None
    
    try:
        download_manager.start_download(download_id)
        
        # Progress callback
        last_update = [0]
        
        def progress_callback(current, total):
            now = time.time()
            if now - last_update[0] >= 3:
                last_update[0] = now
                percent = (current / total * 100) if total > 0 else 0
                bar = make_progress_bar(percent)
                # ذخیره برای استفاده در صورت نیاز
                context.user_data['download_progress'] = {
                    'current': current,
                    'total': total,
                    'percent': percent
                }
        
        # دانلود
        file_path, info = youtube_dl.download(
            url,
            user_id,
            audio_only=False,
            progress_callback=progress_callback
        )
        
        # بررسی لغو
        if download_manager.is_cancelled(download_id):
            await msg.edit_text("🚫 **دانلود لغو شد.**")
            if file_path and file_path.exists():
                file_path.unlink()
            return
        
        file_size = file_path.stat().st_size
        
        # آپلود به Google Drive
        drive = get_drive_service(user_id)
        drive_uploaded = False
        
        if drive:
            try:
                await msg.edit_text(
                    f"📤 **در حال آپلود به Google Drive...**\n\n"
                    f"📁 `{file_path.name}`\n"
                    f"📏 `{format_bytes(file_size)}`",
                    parse_mode="Markdown"
                )
                
                # Progress برای آپلود
                upload_last = [0]
                def upload_progress(current, total):
                    now = time.time()
                    if now - upload_last[0] >= 3:
                        upload_last[0] = now
                
                drive.upload_file(
                    user_id,
                    file_path,
                    progress_callback=upload_progress
                )
                drive_uploaded = True
                
            except Exception as e:
                print(f"Drive upload failed: {e}")
        
        # ارسال فایل به تلگرام اگر زیر 50MB باشه
        if file_size < 50 * 1024 * 1024:
            await msg.edit_text("📤 **در حال ارسال فایل به تلگرام...**", parse_mode="Markdown")
            
            try:
                await update.message.reply_video(
                    video=open(file_path, "rb"),
                    caption=(
                        f"🎬 {info.get('title', 'Unknown')[:100]}\n"
                        f"📏 {format_bytes(file_size)}"
                        f"{' | 💾 Drive' if drive_uploaded else ''}"
                    ),
                    supports_streaming=True,
                    duration=info.get('duration', 0),
                    width=info.get('width', 0),
                    height=info.get('height', 0)
                )
            except Exception as e:
                # اگه ویدیو نبود، document بفرست
                await update.message.reply_document(
                    document=open(file_path, "rb"),
                    caption=f"📏 {format_bytes(file_size)}{' | 💾 Drive' if drive_uploaded else ''}"
                )
        
        # پیام نهایی
        final_text = (
            f"✅ **دانلود کامل شد!**\n\n"
            f"📁 `{file_path.name}`\n"
            f"📏 `{format_bytes(file_size)}`\n"
        )
        
        if drive_uploaded:
            final_text += "💾 **Google Drive** | ✅ آپلود شد\n"
        else:
            final_text += "⚠️ برای آپلود خودکار به Drive، `/login` بزنید.\n"
        
        final_text += f"\n🎬 `{info.get('title', 'Unknown')[:100]}`"
        
        await msg.edit_text(final_text, parse_mode="Markdown")
        
        # ثبت در تاریخچه
        db.add_history(user_id, "youtube", url, str(file_path), file_size)
        db.update_stats(user_id, "youtube", file_size)
        
    except Exception as e:
        error_msg = str(e)
        
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            await msg.edit_text(
                "❌ **یوتیوب نیاز به احراز هویت دارد!**\n\n"
                "🔧 **راه حل:**\n"
                "1. فایل cookies.txt را بفرستید\n"
                "2. روی آن ریپلای کنید و `/cookie` بزنید\n"
                "3. دوباره دانلود را امتحان کنید\n\n"
                "📚 راهنما: از افزونه Get cookies.txt LOCALLY استفاده کنید",
                parse_mode="Markdown"
            )
        elif "Requested format" in error_msg:
            await msg.edit_text(
                f"❌ **فرمت درخواستی در دسترس نیست**\n\n"
                f"از `/formats {url}` برای دیدن فرمت‌های موجود استفاده کنید.",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ **خطا در دانلود:**\n`{error_msg[:300]}`",
                parse_mode="Markdown"
            )
    
    finally:
        download_manager.finish_download(download_id)
        # پاکسازی فایل بعد از ۱ ساعت
        if file_path:
            asyncio.create_task(cleanup_file(file_path))

# ============================================
# دانلود MP3 از یوتیوب
# ============================================

async def mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "📝 **نحوه استفاده:**\n`/mp3 URL`\n\n"
            "مثال:\n`/mp3 https://youtube.com/watch?v=...`",
            parse_mode="Markdown"
        )
        return
    
    url = context.args[0]
    download_id = download_manager.add_download(user_id, url, "YouTube MP3")
    
    msg = await update.message.reply_text(
        "⏳ **در حال دانلود MP3...**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(download_id)
    )
    
    file_path = None
    
    try:
        download_manager.start_download(download_id)
        
        # دانلود صدا
        file_path, info = youtube_dl.download(
            url,
            user_id,
            audio_only=True
        )
        
        # بررسی لغو
        if download_manager.is_cancelled(download_id):
            await msg.edit_text("🚫 **دانلود لغو شد.**")
            if file_path and file_path.exists():
                file_path.unlink()
            return
        
        file_size = file_path.stat().st_size
        
        # آپلود به Google Drive
        drive = get_drive_service(user_id)
        drive_uploaded = False
        
        if drive:
            try:
                await msg.edit_text("📤 **در حال آپلود به Google Drive...**", parse_mode="Markdown")
                drive.upload_file(user_id, file_path)
                drive_uploaded = True
            except Exception as e:
                print(f"Drive upload failed: {e}")
        
        # ارسال فایل صوتی
        if file_size < 50 * 1024 * 1024:
            await msg.edit_text("📤 **در حال ارسال فایل صوتی...**", parse_mode="Markdown")
            
            try:
                await update.message.reply_audio(
                    audio=open(file_path, "rb"),
                    caption=(
                        f"🎵 {info.get('title', 'Unknown')[:100]}\n"
                        f"📏 {format_bytes(file_size)}"
                        f"{' | 💾 Drive' if drive_uploaded else ''}"
                    ),
                    title=info.get('title', 'Unknown')[:100],
                    performer=info.get('uploader', 'Unknown')[:100],
                    duration=info.get('duration', 0)
                )
            except Exception as e:
                await update.message.reply_document(
                    document=open(file_path, "rb"),
                    caption=f"🎵 MP3 | 📏 {format_bytes(file_size)}"
                )
        
        # پیام نهایی
        final_text = (
            f"✅ **MP3 آماده!**\n\n"
            f"🎵 `{file_path.name}`\n"
            f"📏 `{format_bytes(file_size)}`\n"
        )
        
        if drive_uploaded:
            final_text += "💾 **Google Drive** | ✅\n"
        else:
            final_text += "⚠️ `/login` برای آپلود خودکار\n"
        
        final_text += f"\n🎬 منبع: `{info.get('title', 'Unknown')[:100]}`"
        
        await msg.edit_text(final_text, parse_mode="Markdown")
        
        # ثبت در تاریخچه
        db.add_history(user_id, "youtube_mp3", url, str(file_path), file_size)
        db.update_stats(user_id, "youtube", file_size)
        
    except Exception as e:
        error_msg = str(e)
        
        if "Sign in to confirm" in error_msg:
            await msg.edit_text(
                "❌ **نیاز به cookies.txt**\n"
                "فایل cookies را بفرستید و `/cookie` بزنید.",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ **خطا:**\n`{error_msg[:300]}`",
                parse_mode="Markdown"
            )
    
    finally:
        download_manager.finish_download(download_id)
        # پاکسازی
        if file_path:
            asyncio.create_task(cleanup_file(file_path))

# ============================================
# پاکسازی فایل بعد از مدتی
# ============================================

async def cleanup_file(file_path, delay=3600):
    """حذف فایل بعد از delay ثانیه (پیش‌فرض ۱ ساعت)"""
    await asyncio.sleep(delay)
    try:
        if file_path and file_path.exists():
            file_path.unlink()
            print(f"Cleaned up: {file_path}")
    except Exception as e:
        print(f"Cleanup error: {e}")
