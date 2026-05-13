FROM python:3.11-slim

WORKDIR /app

# نصب ffmpeg
RUN apt-get update && apt-get install -y ffmpeg aria2 && rm -rf /var/lib/apt/lists/*

# نصب پیش‌نیازها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد
COPY . .

# ساخت پوشه‌ها
RUN mkdir -p data/tokens downloads logs cookies

# اجرا
CMD ["python", "main.py"]
