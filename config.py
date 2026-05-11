import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "AzuDlBot")

# Pyrogram
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:j4gsQEzwx3HVnv1GBYxc@botty-ols-service:27017/admin")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

# Downloads
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "downloads")
CHUNK_SIZE = 50 * 1024 * 1024  # 50MB
