from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import time
import threading
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def cleanup_old_files():
    while True:
        time.sleep(300)
        try:
            now = time.time()
            for f in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, f)
                if os.path.isfile(filepath) and os.stat(filepath).st_mtime < now - 900:
                    os.remove(filepath)
        except Exception as e:
            pass

threading.Thread(target=cleanup_old_files, daemon=True).start()

# -------------------------------------------------------------
# الإعدادات السحرية لتخطي حظر يوتيوب باستخدام الكوكيز
# -------------------------------------------------------------
ydl_base_opts = {
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'geo_bypass': True,
    'extractor_retries': 3,
    # هنا يتم توجيه yt_dlp لاستخدام ملف الكوكيز
    'cookiefile': 'cookies.txt', 
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }
}

@app.route('/api/extract', methods=['POST'])
def extract():
    url = None
    if request.is_json:
        url = request.json.get('url')
    else:
        url = request.form.get('url')
        
    if not url:
        return jsonify({'status': 'error', 'message': 'No URL provided'}), 400

    opts = ydl_base_opts.copy()
    opts['skip_download'] = True

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Video')
            url_direct = info.get('url', '')
            formats = info.get('formats', [])
            
            available_formats = []
            server_url = request.host_url.rstrip('/')
            
            available_formats.append({
                'format_id': '1080p_server_merged',
                'quality': '1080p',
                'format_note': 'فيديو 1080p (تحميل سريع ⚡)',
                'resolution': '1080p',
                'ext': 'mp4',
                'url': f"{server_url}/api/download?url={url}",
                'acodec': 'mp4a', 
                'vcodec': 'avc1',
                'filesize': None
            })
            
            available_formats.append({
                'format_id': 'server_audio_mp3',
                'quality': 'Audio',
                'format_note': 'صوت عالي الجودة MP3 (تحميل سريع ⚡)',
                'resolution': 'Audio',
                'ext': 'mp3',
                'url': f"{server_url}/api/download_audio?url={url}",
                'acodec': 'mp3', 
                'vcodec': 'none',
                'filesize': None
            })

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

@app.route('/api/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    
    filename = f"video_{uuid.uuid4().hex}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    opts = ydl_base_opts.copy()
    opts.update({
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        'outtmpl': filepath,
        'merge_output_format': 'mp4',
    })
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return send_file(filepath, as_attachment=True, download_name="Boykta_Video.mp4")
    except Exception as e:
        return str(e), 500

@app.route('/api/download_audio', methods=['GET'])
def download_audio():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    
    base_name = f"audio_{uuid.uuid4().hex}"
    filepath = os.path.join(DOWNLOAD_DIR, base_name)
    
    opts = ydl_base_opts.copy()
    opts.update({
        'format': 'bestaudio/best',
        'outtmpl': filepath + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    })
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        final_file = filepath + '.mp3'
        return send_file(final_file, as_attachment=True, download_name="Boykta_Audio.mp3")
    except Exception as e:
        return str(e), 500

@app.route('/', methods=['GET'])
def home():
    return "Boykta Backend is Running Smoothly! 🚀"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
