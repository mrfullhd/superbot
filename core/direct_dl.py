import subprocess
import time
import re
from pathlib import Path
from utils.helpers import sanitize_name, format_bytes
import config

class DirectDownloader:
    def download(self, url, user_id, folder_name="", progress_callback=None):
        """
        دانلود مستقیم با aria2c
        """
        folder_name = sanitize_name(folder_name) if folder_name else "Direct"
        save_dir = Path(config.DOWNLOAD_PATH) / str(user_id) / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        # استخراج نام فایل از URL
        filename = url.split("/")[-1].split("?")[0] or "download.bin"
        filename = sanitize_name(filename)
        file_path = save_dir / filename

        # ساخت دستور aria2c
        cmd = [
            "aria2c",
            "--max-connection-per-server=16",
            "--split=16",
            "--min-split-size=1M",
            "--dir=" + str(save_dir),
            "--out=" + filename,
            "--console-log-level=error",
            "--summary-interval=1",
            url
        ]

        # اجرای فرآیند
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        # خواندن خروجی برای پیشرفت
        total_size = None
        downloaded = 0
        for line in process.stdout:
            # نمونه خروجی: [#...] 12.3MiB/45.6MiB(27%) ...
            match = re.search(r'(\d+(?:\.\d+)?)([KMGT]?iB)/(\d+(?:\.\d+)?)([KMGT]?iB)\((\d+)%\)', line)
            if match:
                downloaded_str = match.group(1) + match.group(2)
                total_str = match.group(3) + match.group(4)
                percent = int(match.group(5))
                # تبدیل به بایت (ساده‌شده)
                # می‌توانید از کتابخانه humanfriendly استفاده کنید، ولی اینجا تقریبی
                # بهتر است از پارس اعداد استفاده نشود چون aria2 خودش خروجی می‌دهد.
                if progress_callback:
                    # ارسال درصد به callback (درصد)
                    progress_callback(percent, 100)
            # همچنین می‌توان خطاها را گرفت

        process.wait()

        if process.returncode != 0:
            raise Exception("aria2c download failed")

        if not file_path.exists():
            raise Exception("File not found after download")

        return file_path

direct_dl = DirectDownloader()
