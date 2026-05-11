# core/uploader.py

import os
import glob
import time
import asyncio
import concurrent.futures
from pathlib import Path
from pyrogram import Client
import config

# پاک کردن session‌های قدیمی و قفل شده
for f in glob.glob("azu_upload*"):
    try:
        os.remove(f)
    except:
        pass

for f in glob.glob("*.session"):
    try:
        os.remove(f)
    except:
        pass

# ThreadPoolExecutor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# Pyrogram client با timeout بیشتر
pyro_app = Client(
    "azu_upload_new",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    no_updates=True,
    workdir="/app/",
    sleep_threshold=60,
    retry=True
)

async def init_pyrogram():
    """شروع Pyrogram با مدیریت خطا"""
    try:
        if not pyro_app.is_connected:
            await pyro_app.start()
            print("✅ Pyrogram started")
    except Exception as e:
        # پاک کردن session و تلاش دوباره
        print(f"Pyrogram start error: {e}")
        for f in glob.glob("azu_upload_new*"):
            try:
                os.remove(f)
            except:
                pass
        await asyncio.sleep(2)
        await pyro_app.start()
        print("✅ Pyrogram started (retry)")

async def download_from_telegram(message, file_path, progress_callback=None):
    """دانلود فایل از تلگرام با Pyrogram - بدون محدودیت حجم"""
    try:
        await init_pyrogram()
    except Exception as e:
        raise Exception(f"Pyrogram connection failed: {e}")
    
    try:
        pyro_msg = await pyro_app.get_messages(message.chat.id, message.message_id)
        
        def pyro_progress(current, total):
            if progress_callback:
                progress_callback(current, total)
        
        await pyro_app.download_media(
            message=pyro_msg,
            file_name=str(file_path),
            progress=pyro_progress
        )
        
        return file_path
        
    except Exception as e:
        error_msg = str(e)
        if "EOF" in error_msg or "database is locked" in error_msg:
            # پاک کردن session و تلاش دوباره
            await pyro_app.stop()
            for f in glob.glob("azu_upload_new*"):
                try:
                    os.remove(f)
                except:
                    pass
            await asyncio.sleep(3)
            await pyro_app.start()
            
            # تلاش مجدد
            pyro_msg = await pyro_app.get_messages(message.chat.id, message.message_id)
            await pyro_app.download_media(
                message=pyro_msg,
                file_name=str(file_path),
                progress=pyro_progress if progress_callback else None
            )
        else:
            raise e
    
    return file_path

async def upload_to_drive_async(drive_service, user_id, file_path, progress_callback=None):
    """آپلود فایل به Google Drive در thread جدا"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        drive_service.upload_file,
        user_id,
        file_path,
        progress_callback
    )
    return result
