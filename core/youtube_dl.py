from pathlib import Path
from yt_dlp import YoutubeDL
from core.database import db
from utils.helpers import sanitize_name
import config


class YouTubeDownloader:
    def __init__(self):
        pass

    # =========================================
    # COOKIES HANDLING
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
    # GET FORMATS (FOR INLINE BUTTONS)
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
                if not f.get("format_id"):
                    continue

                formats.append({
                    "format_id": f["format_id"],
                    "ext": f.get("ext", ""),
                    "resolution": f.get("resolution") or f.get("height"),
                    "vcodec": f.get("vcodec", "none"),
                    "acodec": f.get("acodec", "none"),
                    "filesize": f.get("filesize") or f.get("filesize_approx", 0),
                })

        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "formats": formats[:25]
        }

    # =========================================
    # DOWNLOAD ENGINE (STABLE + FALLBACK)
    # =========================================
    def download(self, url, user_id, folder_name="",
                 audio_only=False, format_id=None,
                 progress_callback=None):

        folder_name = sanitize_name(folder_name) if folder_name else "YouTube"
        save_dir = Path(config.DOWNLOAD_PATH) / str(user_id) / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        # =====================================
        # FORMAT SELECTION LOGIC
        # =====================================
        if audio_only:
            format_selection = "bestaudio/best"
        else:
            # انتخاب کاربر یا fallback امن
            format_selection = format_id or "bv*+ba/best"

        postprocessors = []

        if audio_only:
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320"
            })
        else:
            postprocessors.append({"key": "FFmpegMetadata"})

        options = {
            "format": format_selection,
            "outtmpl": str(save_dir / "%(title).200s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 30,
            "postprocessors": postprocessors,
            "noplaylist": True,
        }

        # =====================================
        # COOKIES SUPPORT
        # =====================================
        cookies_path = self.get_cookies_path(user_id)
        if cookies_path:
            options["cookiefile"] = cookies_path

        # =====================================
        # PROXY SUPPORT (optional)
        # =====================================
        if getattr(config, "PROXY_URL", None):
            options["proxy"] = config.PROXY_URL

        # =====================================
        # DOWNLOAD
        # =====================================
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            file_path = Path(filename)

            # fix audio extension
            if audio_only:
                file_path = file_path.with_suffix(".mp3")

            return file_path, info

        # =====================================
        # FALLBACK (VERY IMPORTANT)
        # =====================================
        except Exception as e:
            error = str(e)

            # اگر فرمت مشکل داشت → fallback امن
            if "Requested format is not available" in error:
                options["format"] = "bv*+ba/best"

                with YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                file_path = Path(filename)
                return file_path, info

            raise e


# =========================================
# SINGLETON
# =========================================
youtube_dl = YouTubeDownloader()
