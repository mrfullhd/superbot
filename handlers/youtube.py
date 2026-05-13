import asyncio
import time
from telegram import Update
from telegram.ext import ContextTypes
from core.youtube_dl import youtube_dl
from core.google_drive import get_drive_service
from core.downloader import download_manager
from core.database import db
from utils.helpers import format_bytes, make_progress_bar
from keyboards.inline import cancel_keyboard, formats_keyboard

async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("📝 `/yt URL`\nمثال: `/yt https://youtube.com/watch?v=...`", parse_mode="Markdown")
        return
    
    url = context.args[0]
    download_id = download_manager.add_download(user_id, url, "YouTube Video")
    
    msg = await update.message.reply_text(
        "⏳ **در حال دریافت اطلاعات ویدیو...**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(download_id)
    )
    
    try:
        # دانلود
        download_manager.start_download(download_id)
        
        file_path, info = youtube_dl.download(
            url, user_id,
            progress_callback=lambda c, t: None  # می‌تونیم progress bar اضافه کنیم
        )
        
        if download_manager.is_cancelled(download_id):
            await msg.edit_text("🚫 دانلود لغو شد.")
            return
        
        file_size = file_path.stat().st_size
        
        # آپلود به Drive
        drive = get_drive_service(user_id)
        if drive:
            await msg.edit_text("📤 **در حال آپلود به Google Drive...**", parse_mode="Markdown")
            
            try:
                drive.upload_file(user_id, file_path)
                await msg.edit_text(
                    f"✅ **دانلود و آپلود کامل شد!**\n\n"
                    f"📁 `{file_path.name}`\n"
                    f"📏 `{format_bytes(file_size)}`\n"
                    f"💾 **Google Drive** | ✅",
                    parse_mode="Markdown"
                )
            except Exception as e:
                # ارسال فایل به تلگرام
                if file_size < 50 * 1024 * 1024:
                    await msg.edit_text("📤 **در حال ارسال فایل...**", parse_mode="Markdown")
                    await update.message.reply_video(
                        video=open(file_path, "rb"),
                        caption=f"📏 {format_bytes(file_size)}",
                        supports_streaming=True
                    )
                
                await msg.edit_text(
                    f"✅ **دانلود کامل شد!**\n\n"
                    f"📁 `{file_path.name}`\n"
                    f"📏 `{format_bytes(file_size)}`\n"
                    f"⚠️ برای آپلود خودکار، `/login` بزنید.",
                    parse_mode="Markdown"
                )
        else:
            if file_size < 50 * 1024 * 1024:
                await update.message.reply_video(
                    video=open(file_path, "rb"),
                    caption=f"📏 {format_bytes(file_size)}",
                    supports_streaming=True
                )
            
            await msg.edit_text(
                f"✅ **دانلود کامل شد!**\n\n"
                f"📁 `{file_path.name}`\n"
                f"📏 `{format_bytes(file_size)}`\n"
                f"💡 `/login` بزنید تا فایل‌ها خودکار به Google Drive آپلود شوند.",
                parse_mode="Markdown"
            )
        
        db.add_history(user_id, "youtube", url, str(file_path), file_size)
        db.update_stats(user_id, "youtube", file_size)
        
    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n`{str(e)[:200]}`", parse_mode="Markdown")
    finally:
        download_manager.finish_download(download_id)
        # پاکسازی فایل بعد از ۱ ساعت
        asyncio.create_task(cleanup_file(file_path))

async def cleanup_file(file_path, delay=3600):
    await asyncio.sleep(delay)
    try:
        if file_path.exists():
            file_path.unlink()
    except:
        pass
