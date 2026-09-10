FROM python:3.10-slim

# تحديث النظام وتثبيت أداة FFmpeg الأساسية لدمج الفيديوهات والصوتيات
RUN apt-get update && apt-get install -y ffmpeg

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات أولاً لضمان سرعة بناء الحاوية في المرات القادمة
COPY requirements.txt .

# تثبيت مكتبات بايثون المطلوبة دون الاحتفاظ بملفات الكاش لتوفير المساحة
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع إلى مجلد العمل
COPY . .

# تشغيل السيرفر باستخدام Gunicorn مع تمديد مهلة الاتصال إلى 10 دقائق (600 ثانية)
# وربط التطبيق بالمنفذ الديناميكي الذي توفره منصة Railway
CMD gunicorn --timeout 600 -b 0.0.0.0:$PORT app:app
