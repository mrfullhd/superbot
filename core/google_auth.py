import os
import json
import config
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from core.database import db

SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_CONFIG = {
    "web": {
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [config.GOOGLE_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

class GoogleDriveAuth:
    def __init__(self):
        self.flows = {}
    
    def get_auth_url(self, user_id):
        """تولید لینک OAuth برای کاربر"""
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=config.GOOGLE_REDIRECT_URI
        )
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            state=str(user_id)
        )
        
        self.flows[state] = flow
        return auth_url, state
    
    def exchange_code(self, user_id, code, state):
        """تبدیل کد به توکن"""
        try:
            flow = self.flows.get(state)
            if not flow:
                flow = Flow.from_client_config(
                    CLIENT_CONFIG,
                    scopes=SCOPES,
                    redirect_uri=config.GOOGLE_REDIRECT_URI,
                    state=state
                )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # دریافت ایمیل کاربر
            drive_service = build('drive', 'v3', credentials=credentials)
            about = drive_service.about().get(fields="user").execute()
            email = about.get('user', {}).get('emailAddress', 'unknown')
            
            token_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            db.save_token(user_id, token_data, email)
            db.add_user(user_id)
            
            if state in self.flows:
                del self.flows[state]
            
            return True, email
            
        except Exception as e:
            return False, str(e)
    
    def get_drive_service(self, user_id):
        """ساخت سرویس Drive برای کاربر"""
        token_data = db.get_token(user_id)
        if not token_data:
            return None
        
        credentials = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        if credentials.expired:
            try:
                credentials.refresh(Request())
                new_token_data = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                db.save_token(user_id, new_token_data, None)
            except Exception as e:
                print(f"Refresh token failed for user {user_id}: {e}")
                db.delete_token(user_id)
                return None
        
        return build('drive', 'v3', credentials=credentials)
    
    def is_authenticated(self, user_id):
        return db.is_authenticated(user_id)
    
    def logout(self, user_id):
        db.delete_token(user_id)

google_auth = GoogleDriveAuth()
