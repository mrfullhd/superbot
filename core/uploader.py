import time
import asyncio
import concurrent.futures
from pathlib import Path
from pyrogram import Client
import config

# ThreadPoolExecutor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# Pyrogram client
pyro_app = Client(
    "azu_upload",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    no_updates=True
)

async def init_pyrogram():
    if not pyro_app.is_connected:
        await pyro_app.start()
        print("✅ Pyrogram started")

async def download_from_telegram(message, file_path, progress_callback=None):
    """دانلود فایل از تلگرام با Pyrogram - بدون محدودیت حجم"""
    await init_pyrogram()
    
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
