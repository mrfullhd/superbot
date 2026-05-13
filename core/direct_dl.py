import requests
from pathlib import Path
from utils.helpers import sanitize_name
import config

class DirectDownloader:
    def __init__(self):
        pass
    
    def download(self, url, user_id, folder_name="", progress_callback=None):
        """دانلود مستقیم فایل"""
        folder_name = sanitize_name(folder_name) if folder_name else "Direct"
        save_dir = Path(config.DOWNLOAD_PATH) / str(user_id) / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)
        
        proxies = {"http": config.PROXY_URL, "https": config.PROXY_URL} if config.PROXY_URL else None
        
        response = requests.get(url, stream=True, timeout=60, proxies=proxies)
        response.raise_for_status()
        
        filename = url.split("/")[-1].split("?")[0] or "download.bin"
        filename = sanitize_name(filename)
        file_path = save_dir / filename
        
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded, total)
        
        return file_path

direct_dl = DirectDownloader()
