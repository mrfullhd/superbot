from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🔍 جستجوی یوتیوب", callback_data="menu_search")],
        [InlineKeyboardButton("📥 دانلود ویدیو", callback_data="menu_yt"),
         InlineKeyboardButton("🎵 دانلود صدا", callback_data="menu_mp3")],
        [InlineKeyboardButton("📤 آپلود به Drive", callback_data="menu_upload")],
        [InlineKeyboardButton("🔐 اتصال به Google Drive", callback_data="menu_login")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="menu_settings"),
         InlineKeyboardButton("📊 آمار", callback_data="menu_stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

def formats_keyboard(formats, url):
    keyboard = []
    for i, fmt in enumerate(formats[:10]):
        label = f"{fmt['resolution']} - {fmt['ext']}"
        if fmt.get('filesize'):
            label += f" ({format_bytes_static(fmt['filesize'])})"
        keyboard.append([InlineKeyboardButton(
            label,
            callback_data=f"fmt_{fmt['format_id']}_{url[:50]}"
        )])
    return InlineKeyboardMarkup(keyboard)

def quality_settings():
    keyboard = [
        [InlineKeyboardButton("1080p", callback_data="quality_1080"),
         InlineKeyboardButton("720p", callback_data="quality_720")],
        [InlineKeyboardButton("480p", callback_data="quality_480"),
         InlineKeyboardButton("360p", callback_data="quality_360")],
        [InlineKeyboardButton("بهترین کیفیت", callback_data="quality_best")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)

def format_bytes_static(size):
    size = float(size) if size else 0
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def cancel_keyboard(download_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🚫 لغو دانلود", callback_data=f"cancel_{download_id}")
    ]])

def login_keyboard(auth_url):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔗 ورود به Google Drive", url=auth_url)
    ]])

def search_results_keyboard(results):
    keyboard = []
    for i, result in enumerate(results[:5]):
        keyboard.append([InlineKeyboardButton(
            f"{result['title'][:50]}",
            callback_data=f"dl_{result['id']}"
        )])
    return InlineKeyboardMarkup(keyboard)
