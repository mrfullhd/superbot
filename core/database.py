import os
from datetime import datetime
import pymongo
from pymongo import MongoClient
import config

class Database:
    def __init__(self, mongo_uri=None):
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://admin:j4gsQEzwx3HVnv1GBYxc@botty-ols-service:27017/admin")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client["azudl_bot"]
        self.users = self.db["users"]
        self.tokens = self.db["tokens"]
        self.history = self.db["history"]
        self.cookies = self.db["cookies"]
        self.stats = self.db["stats"]
        self.downloads = self.db["downloads"]

    # ---------- Users ----------
    def add_user(self, user_id, username=None, first_name=None):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "username": username,
                "first_name": first_name,
                "joined_date": datetime.utcnow(),
                "is_banned": False,
                "is_admin": False,
                "settings": {}
            }},
            upsert=True
        )

    def is_banned(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user.get("is_banned", False) if user else False

    def ban_user(self, user_id):
        self.users.update_one({"user_id": user_id}, {"$set": {"is_banned": True}})

    def unban_user(self, user_id):
        self.users.update_one({"user_id": user_id}, {"$set": {"is_banned": False}})

    def get_all_users(self):
        return list(self.users.find({}))

    def user_count(self):
        return self.users.count_documents({})

    # ---------- Tokens (Google Drive) ----------
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

    # ---------- Cookies ----------
    def save_cookies(self, user_id, cookies_data):
        self.cookies.update_one(
            {"user_id": user_id},
            {"$set": {"cookies_data": cookies_data, "added_date": datetime.utcnow()}},
            upsert=True
        )

    def get_cookies(self, user_id):
        doc = self.cookies.find_one({"user_id": user_id})
        return doc.get("cookies_data") if doc else None

    # ---------- History ----------
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
        return list(
            self.history.find({"user_id": user_id})
            .sort("_id", -1)
            .limit(limit)
        )

    # ---------- Stats ----------
    def update_stats(self, user_id, download_type, file_size=0):
        inc = {"total_downloads": 1, "total_size": file_size}
        if download_type == "youtube":
            inc["youtube_downloads"] = 1
        elif download_type == "direct":
            inc["direct_downloads"] = 1
        elif download_type == "upload":
            inc["uploads"] = 1

        self.stats.update_one(
            {"user_id": user_id},
            {"$inc": inc},
            upsert=True
        )

    def get_stats(self, user_id):
        return self.stats.find_one({"user_id": user_id})

    def get_total_stats(self):
        pipeline = [
            {"$group": {
                "_id": None,
                "total_users": {"$sum": 1},
                "total_downloads": {"$sum": "$total_downloads"},
                "total_size": {"$sum": "$total_size"}
            }}
        ]
        result = list(self.stats.aggregate(pipeline))
        if result:
            return result[0]
        return {"total_users": 0, "total_downloads": 0, "total_size": 0}

    # ---------- User Settings ----------
    def get_user_settings(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user.get("settings", {}) if user else {}

    def save_user_settings(self, user_id, settings):
        self.users.update_one({"user_id": user_id}, {"$set": {"settings": settings}})

    # ---------- Downloads (active) ----------
    def add_download(self, user_id, url, file_name):
        doc = {
            "user_id": user_id,
            "url": url,
            "file_name": file_name,
            "status": "pending",
            "progress": 0,
            "start_date": datetime.utcnow()
        }
        result = self.downloads.insert_one(doc)
        return str(result.inserted_id)

    def update_download_status(self, download_id, status, progress=0):
        from bson.objectid import ObjectId
        self.downloads.update_one(
            {"_id": ObjectId(download_id)},
            {"$set": {"status": status, "progress": progress}}
        )

    def get_active_downloads_count(self, user_id):
        return self.downloads.count_documents({
            "user_id": user_id,
            "status": {"$in": ["pending", "downloading"]}
        })

    def cancel_download(self, user_id, download_id):
        from bson.objectid import ObjectId
        self.downloads.update_one(
            {"_id": ObjectId(download_id), "user_id": user_id},
            {"$set": {"status": "cancelled"}}
        )

db = Database()
