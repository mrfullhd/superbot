import os
import time
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from core.google_auth import google_auth
from core.database import db
import config

class GoogleDriveService:
    def __init__(self):
        self.drive_services = {}
    
    def get_service(self, user_id):
        return google_auth.get_drive_service(user_id)
    
    def upload_file(self, user_id, file_path, file_name=None, progress_callback=None):
        """آپلود فایل به Google Drive کاربر"""
        service = self.get_service(user_id)
        if not service:
            raise Exception("کاربر احراز هویت نشده. لطفاً /login را بزنید.")
        
        file_path = Path(file_path)
        if not file_name:
            file_name = file_path.name
        
        file_metadata = {'name': file_name}
        
        media = MediaFileUpload(
            str(file_path),
            resumable=True,
            chunksize=config.CHUNK_SIZE
        )
        
        request = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size, webViewLink'
        )
        
        response = None
        file_size = file_path.stat().st_size
        uploaded = 0
        
        while response is None:
            status, response = request.next_chunk()
            if status:
                uploaded = status.resumable_progress
                if progress_callback:
                    progress_callback(uploaded, file_size)
        
        return response
    
    def create_folder(self, user_id, folder_name, parent_id=None):
        """ساخت پوشه در Drive"""
        service = self.get_service(user_id)
        if not service:
            return None
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    
    def find_folder(self, user_id, folder_name):
        """جستجوی پوشه"""
        service = self.get_service(user_id)
        if not service:
            return None
        
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])
        return folders[0]['id'] if folders else None
    
    def get_or_create_folder(self, user_id, folder_name):
        """یافتن یا ساخت پوشه"""
        folder_id = self.find_folder(user_id, folder_name)
        if not folder_id:
            folder_id = self.create_folder(user_id, folder_name)
        return folder_id
    
    def get_storage_info(self, user_id):
        """اطلاعات فضای ذخیره‌سازی"""
        service = self.get_service(user_id)
        if not service:
            return None
        
        about = service.about().get(fields="storageQuota").execute()
        quota = about.get('storageQuota', {})
        return {
            'limit': int(quota.get('limit', 0)),
            'usage': int(quota.get('usage', 0)),
            'usage_in_drive': int(quota.get('usageInDrive', 0)),
        }

drive_service_singleton = GoogleDriveService()

def get_drive_service(user_id):
    return drive_service_singleton
