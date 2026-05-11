from datetime import datetime
from pymongo import MongoClient
import config

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client["azudl_bot"]
        self.users = self.db["users"]
        self.tokens = self.db["tokens"]
        self.history = self.db["history"]
        self.cookies = self.db["cookies"]
        self.stats = self.db["stats"]

    # Users
    def add_user(self, user_id, username=None, first_name=None):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "username": username,
                "first_name": first_name,
                "joined_date": datetime.utcnow(),
                "is_banned": False,
                "settings": {}
            }},
            upsert=True
        )

    def is_banned(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user.get("is_banned", False) if user else False

    # Tokens (Google Drive)
    def save_token(self, user_id, token_data, drive_email):
        self.tokens.update_one(
            {"user_id": user_id},
            {"$set": {
                "token_data": token_data,
                "drive_email": drive_email,
                "added_date": datetime.utcnow()
            }},
            upsert=True
        )

    def get_token(self, user_id):
        doc = self.tokens.find_one({"user_id": user_id})
        return doc.get("token_data") if doc else None

    def delete_token(self, user_id):
        self.tokens.delete_one({"user_id": user_id})

    def is_authenticated(self, user_id):
        return self.tokens.find_one({"user_id": user_id}) is not None

    # History
    def add_history(self, user_id, type, source, output, file_size, status="completed"):
        self.history.insert_one({
            "user_id": user_id,
            "type": type,
            "source": source,
            "output": output,
            "file_size": file_size,
            "status": status,
            "date": datetime.utcnow()
        })

    def get_history(self, user_id, limit=10):
        return list(self.history.find({"user_id": user_id}).sort("_id", -1).limit(limit))

    # Cookies
    def save_cookies(self, user_id, cookies_data):
        self.cookies.update_one(
            {"user_id": user_id},
            {"$set": {"cookies_data": cookies_data, "added_date": datetime.utcnow()}},
            upsert=True
        )

    def get_cookies(self, user_id):
        doc = self.cookies.find_one({"user_id": user_id})
        return doc.get("cookies_data") if doc else None

    # Stats
    def update_stats(self, user_id, download_type, file_size=0):
        inc = {"total_downloads": 1, "total_size": file_size}
        if download_type == "youtube": inc["youtube_downloads"] = 1
        elif download_type == "direct": inc["direct_downloads"] = 1
        elif download_type == "upload": inc["uploads"] = 1
        self.stats.update_one({"user_id": user_id}, {"$inc": inc}, upsert=True)

    def get_stats(self, user_id):
        return self.stats.find_one({"user_id": user_id})

db = Database()
