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

# فتح المنفذ الذي تستخدمه منصة Render
EXPOSE 10000

# تشغيل السيرفر
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
