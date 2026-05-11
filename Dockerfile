FROM python:3.11-slim

WORKDIR /app

# نصب ffmpeg و aria2
RUN apt-get update && \
    apt-get install -y ffmpeg aria2 wget curl && \
    rm -rf /var/lib/apt/lists/*

# بررسی نصب بودن aria2c
RUN which aria2c && aria2c --version

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads logs cookies

CMD ["python", "main.py"]
