from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import time
import threading
import uuid

app = Flask(__name__)

# إنشاء مجلد مؤقت داخل سيرفر Railway لحفظ الفيديوهات المدمجة
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# دالة تنظيف ذكية: تعمل في الخلفية لمسح الفيديوهات القديمة حتى لا تمتلئ مساحة السيرفر
def cleanup_old_files():
    while True:
        time.sleep(1800) # فحص كل نصف ساعة
        try:
            now = time.time()
            for f in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, f)
                # حذف أي ملف مر عليه أكثر من ساعة
                if os.path.isfile(filepath) and os.stat(filepath).st_mtime < now - 3600:
                    os.remove(filepath)
        except Exception as e:
            pass

# تشغيل منظف الملفات في الخلفية
threading.Thread(target=cleanup_old_files, daemon=True).start()

@app.route('/api/extract', methods=['POST'])
def extract():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'status': 'error', 'message': 'No URL provided'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Video')
            url_direct = info.get('url', '')
            formats = info.get('formats', [])
            
            available_formats = []
            
            # --- السحر هنا: إضافة جودة 1080p فائقة مدمجة بواسطة سيرفرنا ---
            # نقوم بصنع رابط يوجه التطبيق نحو المسار السري الخاص بنا للدمج
            server_url = request.host_url.rstrip('/')
            merged_1080p_url = f"{server_url}/api/download?url={url}"
            
            available_formats.append({
                'format_id': '1080p_server_merged',
                'quality': '1080p',
                'format_note': 'FHD 1080p (دمج السيرفر الخارق ⚡)',
                'resolution': '1080p',
                'ext': 'mp4',
                'url': merged_1080p_url,
                'acodec': 'mp4a', # كتابة بيانات وهمية لكي يعبرها فلتر فلاتر
                'vcodec': 'avc1',
                'filesize': None
            })

            # إضافة باقي الجودات التي يوفرها الموقع
            for f in formats:
                available_formats.append({
                    'format_id': f.get('format_id'),
                    'quality': f.get('quality'),
                    'format_note': f.get('format_note'),
                    'resolution': f.get('resolution'),
                    'ext': f.get('ext'),
                    'url': f.get('url'),
                    'acodec': f.get('acodec'),
                    'vcodec': f.get('vcodec'),
                    'filesize': f.get('filesize')
                })

            return jsonify({
                'status': 'success',
                'title': title,
                'url': url_direct,
                'formats': available_formats
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# المسار السري الجديد: يقوم بالتحميل، الدمج عبر FFmpeg، وإرسال الملف النهائي!
@app.route('/api/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    
    # صنع اسم عشوائي للفيديو لمنع التداخل إذا حمّل شخصان في نفس الوقت
    filename = f"video_{uuid.uuid4().hex}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # إعدادات جلب أفضل فيديو (حتى 1080p) + أفضل صوت، ودمجهما
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        'outtmpl': filepath,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        # هذه الخطوة ستتم بسرعة خيالية لأن سيرفرات Railway متصلة بإنترنت جيجابت!
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الملف المدمج إلى تطبيق فلاتر
        return send_file(filepath, as_attachment=True, download_name="ProDownloader_1080p.mp4")
    except Exception as e:
        return str(e), 500

@app.route('/', methods=['GET'])
def home():
    return "Pro Downloader Backend is Running Perfectly! 🚀"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
