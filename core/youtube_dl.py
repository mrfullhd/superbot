from pathlib import Path
from yt_dlp import YoutubeDL
from core.database import db
from utils.helpers import sanitize_name
import config

class YouTubeDownloader:
    def get_cookies_path(self, user_id):
        cookies_data = db.get_cookies(user_id)
        if not cookies_data:
            return None
        cookies_path = Path("cookies") / f"user_{user_id}.txt"
        cookies_path.parent.mkdir(parents=True, exist_ok=True)
        cookies_path.write_text(cookies_data)
        return str(cookies_path)

    def download(self, url, user_id, audio_only=False, progress_callback=None):
        save_dir = Path(config.DOWNLOAD_PATH) / str(user_id) / "YouTube"
        save_dir.mkdir(parents=True, exist_ok=True)

        if audio_only:
            fmt = "bestaudio/best"
            postprocessors = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320"
            }]
        else:
            # فرمت استاندارد سازگار با همه ویدیوها [citation:4][citation:9]
            fmt = "best[height<=1080]/best"
            postprocessors = [{"key": "FFmpegMetadata"}]

        options = {
            "format": fmt,
            "outtmpl": str(save_dir / "%(title).200s.%(ext)s"),
            "merge_output_format": "mp4" if not audio_only else None,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": postprocessors,
            "socket_timeout": 30,
            "noplaylist": True,
        }

        cookies_path = self.get_cookies_path(user_id)
        if cookies_path:
            options["cookiefile"] = cookies_path

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        file_path = Path(filename)
        if audio_only:
            file_path = file_path.with_suffix(".mp3")
        elif file_path.suffix != ".mp4":
            file_path = file_path.with_suffix(".mp4")

        return file_path, info

youtube_dl = YouTubeDownloader()
