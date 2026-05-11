import re
from datetime import datetime

def sanitize_name(text):
    text = str(text or "").strip()
    text = re.sub(r'[\/\\:*?"<>|]', "_", text)
    text = re.sub(r"\s+", " ", text)
    if not text:
        text = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return text[:200]

def format_bytes(size):
    size = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def make_progress_bar(percent, length=15):
    filled = int(percent / 100 * length)
    return "■" * filled + "□" * (length - filled)
def format_duration(seconds):
    if not seconds:
        return "نامشخص"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
