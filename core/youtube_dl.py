from pathlib import Path
from yt_dlp import YoutubeDL
from core.database import db
from utils.helpers import sanitize_name
import config

class YouTubeDownloader:
    def __init__(self):
        pass
    
    def get_cookies_path(self, user_id):
        """دریافت مسیر فایل cookies کاربر"""
        cookies_data = db.get_cookies(user_id)
        if not cookies_data:
            return None
        
        cookies_path = Path(f"cookies/user_{user_id}.txt")
        cookies_path.parent.mkdir(parents=True, exist_ok=True)
        cookies_path.write_text(cookies_data)
        return str(cookies_path)
    
    def get_formats(self, url, user_id=None):
        """دریافت فرمت‌های موجود"""
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
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats.append({
                        'format_id': f['format_id'],
                        'ext': f['ext'],
                        'resolution': f.get('resolution', 'audio only'),
                        'filesize': f.get('filesize', f.get('filesize_approx', 0)),
                        'note': f.get('format_note', '')
                    })
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'formats': formats[:20]
            }
    
    def download(self, url, user_id, folder_name="", audio_only=False, format_id=None, progress_callback=None):
        """دانلود ویدیو/صدا"""
        folder_name = sanitize_name(folder_name) if folder_name else "YouTube"
        save_dir = Path(config.DOWNLOAD_PATH) / str(user_id) / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # انتخاب فرمت هوشمند
        if audio_only:
            format_selection = format_id or "bestaudio/best"
        else:
            if format_id:
                format_selection = format_id
            else:
                # تلاش برای پیدا کردن بهترین فرمت موجود به ترتیب اولویت
                format_selection = (
                    "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
                    "bestvideo[height<=1080]+bestaudio/"
                    "best[height<=1080]/"
                    "bestvideo+bestaudio/"
                    "best"
                )
        
        # تنظیمات post-processing
        if audio_only:
            postprocessors = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320"
            }]
        else:
            postprocessors = [{"key": "FFmpegMetadata"}]
        
        options = {
            "format": format_selection,
            "outtmpl": str(save_dir / "%(title).200s.%(ext)s"),
            "merge_output_format": "mp4",
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": postprocessors,
            "socket_timeout": 30,
            "ignoreerrors": False,
            "nooverwrites": False,
        }
        
        # اضافه کردن progress hook
        if progress_callback:
            options["progress_hooks"] = [lambda d: self._progress_hook(d, progress_callback)]
        
        # اضافه کردن cookies
        cookies_path = self.get_cookies_path(user_id)
        if cookies_path:
            options["cookiefile"] = cookies_path
        
        # اضافه کردن پروکسی
        if config.PROXY_URL:
            options["proxy"] = config.PROXY_URL
        
        # دانلود
        file_path = None
        info = None
        
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            
            file_path = Path(filename)
            
            # اصلاح پسوند فایل
            if audio_only:
                if file_path.suffix != ".mp3":
                    actual_file = file_path.with_suffix(".mp3")
                    if actual_file.exists():
                        file_path = actual_file
            else:
                for ext in [".mp4", ".mkv", ".webm"]:
                    test_path = file_path.with_suffix(ext)
                    if test_path.exists():
                        file_path = test_path
                        break
            
            return file_path, info
            
        except Exception as e:
            error_msg = str(e)
            
            # مدیریت خطای فرمت در دسترس نیست
            if "Requested format is not available" in error_msg:
                # تلاش با فرمت fallback
                options["format"] = "best"
                
                with YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                
                file_path = Path(filename)
                for ext in [".mp4", ".mkv", ".webm"]:
                    test_path = file_path.with_suffix(ext)
                    if test_path.exists():
                        file_path = test_path
                        break
                
                return file_path, info
            else:
                raise e
    
    def _progress_hook(self, d, callback):
        """هندلر پیشرفت دانلود"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if callback and total > 0:
                callback(downloaded, total)
    
    def search(self, query, limit=5):
        """جستجوی ویدیو در یوتیوب"""
        options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "force_generic_extractor": False,
        }
        
        search_url = f"ytsearch{limit}:{query}"
        
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(search_url, download=False)
        
        results = []
        for entry in info.get('entries', []):
            if entry:
                results.append({
                    'title': entry.get('title', 'Unknown'),
                    'url': entry.get('url', entry.get('webpage_url', '')),
                    'duration': entry.get('duration', 0),
                    'id': entry.get('id', ''),
                })
        
        return results
    
    def get_playlist_info(self, url, user_id=None):
        """اطلاعات playlist"""
        options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
        }
        
        cookies_path = self.get_cookies_path(user_id) if user_id else None
        if cookies_path:
            options["cookiefile"] = cookies_path
        
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        
        return {
            'title': info.get('title', 'Unknown'),
            'count': len(info.get('entries', [])),
            'entries': [{'title': e.get('title', ''), 'url': e.get('url', '')} for e in info.get('entries', [])]
        }

youtube_dl = YouTubeDownloader()
