import re
import time
import shutil
from pathlib import Path
from datetime import datetime
import config
from core.database import db
from utils.helpers import sanitize_name, format_bytes

class DownloadManager:
    def __init__(self):
        self.active_downloads = {}
    
    def add_download(self, user_id, url, file_name):
        return db.add_download(user_id, url, file_name)
    
    def cancel_download(self, user_id, download_id):
        download_id = int(download_id)
        if download_id in self.active_downloads:
            self.active_downloads[download_id] = False
        db.cancel_download(user_id, download_id)
        return True
    
    def is_cancelled(self, download_id):
        return not self.active_downloads.get(download_id, True)
    
    def start_download(self, download_id):
        self.active_downloads[download_id] = True
    
    def finish_download(self, download_id):
        if download_id in self.active_downloads:
            del self.active_downloads[download_id]
    
    def get_active_count(self, user_id):
        return db.get_active_downloads_count(user_id)

download_manager = DownloadManager()
