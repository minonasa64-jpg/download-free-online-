FROM python:3.10-slim

# تحديث النظام وتثبيت FFmpeg لدمج الفيديوهات
RUN apt-get update && apt-get install -y ffmpeg

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع
COPY requirements.txt .

# تثبيت مكتبات بايثون
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# تشغيل السيرفر مع ربطه بمنفذ Railway الديناميكي
CMD gunicorn -b 0.0.0.0:$PORT app:app
