import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "superdllbot")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")

# Admin
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/database.db")

# Downloads
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "downloads")
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "52428800"))  # 50MB

# Proxy (optional)
PROXY_URL = os.getenv("PROXY_URL", "")
