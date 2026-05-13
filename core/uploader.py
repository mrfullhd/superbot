import os
import glob
import asyncio
import concurrent.futures
from pathlib import Path

from pyrogram import Client
import config


# =========================================
# CLEAN OLD SESSIONS
# =========================================
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


executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)


# =========================================
# PYROGRAM CLIENT (MTProto)
# =========================================
pyro_app = Client(
    "azu_upload_new",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    no_updates=True,
    workdir="/app/",
    sleep_threshold=60
)


# =========================================
# INIT PYROGRAM SAFE
# =========================================
async def init_pyrogram():
    try:
        if not pyro_app.is_connected:
            await pyro_app.start()
            print("✅ Pyrogram started")

    except Exception as e:
        print(f"Pyrogram error: {e}")

        # reset session
        for f in glob.glob("azu_upload_new*"):
            try:
                os.remove(f)
            except:
                pass

        await asyncio.sleep(2)
        await pyro_app.start()


# =========================================
# DOWNLOAD FROM TELEGRAM (NO LIMIT)
# =========================================
async def download_from_telegram(message, file_path, progress_callback=None):
    """
    دانلود واقعی از تلگرام با Pyrogram
    بدون محدودیت 20MB bot API
    """

    await init_pyrogram()

    try:
        # گرفتن message واقعی از MTProto
        pyro_msg = await pyro_app.get_messages(
            message.chat.id,
            message.message_id
        )

        def progress(current, total):
            if progress_callback:
                progress_callback(current, total)

        await pyro_app.download_media(
            message=pyro_msg,
            file_name=str(file_path),
            progress=progress
        )

        return file_path

    except Exception as e:
        raise Exception(f"Telegram download failed: {str(e)}")


# =========================================
# DRIVE UPLOAD THREAD SAFE
# =========================================
async def upload_to_drive_async(drive_service, user_id, file_path, progress_callback=None):
    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(
        executor,
        drive_service.upload_file,
        user_id,
        file_path,
        progress_callback
    )

    return result
