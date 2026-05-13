from pathlib import Path
from yt_dlp import YoutubeDL
from core.database import db
from utils.helpers import sanitize_name
import config


class YouTubeDownloader:
    def __init__(self):
        pass

    # =========================================
    # COOKIES
    # =========================================
    def get_cookies_path(self, user_id):
        cookies_data = db.get_cookies(user_id)
        if not cookies_data:
            return None

        cookies_path = Path(f"cookies/user_{user_id}.txt")
        cookies_path.parent.mkdir(parents=True, exist_ok=True)
        cookies_path.write_text(cookies_data)
        return str(cookies_path)

    # =========================================
    # GET FORMATS (SAFE + CLEAN)
    # =========================================
    def get_formats(self, url, user_id=None):
        options = {
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
        }

        cookies_path = self.get_cookies_path(user_id) if user_id else None
        if cookies_path:
            options["cookiefile"] = cookies_path

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = []

            for f in info.get("formats", []):
                fid = f.get("format_id")
                if not fid:
                    continue

                vcodec = f.get("vcodec")
                acodec = f.get("acodec")

                # فقط فرمت‌های واقعی
                if vcodec == "none" and acodec == "none":
                    continue

                formats.append({
                    "format_id": fid,
                    "ext": f.get("ext"),
                    "resolution": f.get("resolution") or f.get("height"),
                    "vcodec": vcodec,
                    "acodec": acodec,
                })

        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "formats": formats[:25]
        }

    # =========================================
    # DOWNLOAD (FIXED + NO FORMAT ERROR)
    # =========================================
    def download(self, url, user_id, folder_name="",
                 audio_only=False, format_id=None,
                 progress_callback=None):

        folder_name = sanitize_name(folder_name) if folder_name else "YouTube"
        save_dir = Path(config.DOWNLOAD_PATH) / str(user_id) / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        # =====================================
        # SAFE FORMAT LOGIC (FIX MAIN ERROR)
        # =====================================
        if audio_only:
            format_selection = "bestaudio/best"
        else:
            if not format_id or format_id == "best":
                format_selection = "bestvideo+bestaudio/best"
            else:
                # مهم: همیشه audio رو اضافه کن
                format_selection = f"{format_id}+bestaudio/bestvideo+bestaudio/best"

        options = {
            "format": format_selection,
            "outtmpl": str(save_dir / "%(title).200s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 30,
            "noplaylist": True,
        }

        # cookies
        cookies_path = self.get_cookies_path(user_id)
        if cookies_path:
            options["cookiefile"] = cookies_path

        # proxy
        if getattr(config, "PROXY_URL", None):
            options["proxy"] = config.PROXY_URL

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            file_path = Path(filename)

            if audio_only:
                file_path = file_path.with_suffix(".mp3")

            return file_path, info

        # =====================================
        # HARD FALLBACK (IMPORTANT)
        # =====================================
        except Exception:
            options["format"] = "best"

            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            return Path(filename), info


youtube_dl = YouTubeDownloader()
