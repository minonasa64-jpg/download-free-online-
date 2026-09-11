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
        time.sleep(300) # الفحص كل 5 دقائق
        try:
            now = time.time()
            for f in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, f)
                if os.path.isfile(filepath) and os.stat(filepath).st_mtime < now - 900:
                    os.remove(filepath)
        except Exception as e:
            pass

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
            
            # خيار دمج السيرفر للفيديو العالي
            server_url = request.host_url.rstrip('/')
            merged_1080p_url = f"{server_url}/api/download?url={url}"
            
            available_formats.append({
                'format_id': '1080p_server_merged',
                'quality': '1080p',
                'format_note': 'FHD 1080p (دمج السيرفر ⚡)',
                'resolution': '1080p',
                'ext': 'mp4',
                'url': merged_1080p_url,
                'acodec': 'mp4a', 
                'vcodec': 'avc1',
                'filesize': None
            })

            # تصفية وفصل الجودات بدقة عالية
            for f in formats:
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                ext = f.get('ext', '')
                
                # إذا كان الصوت صافياً (بدون فيديو)
                is_audio_only = (vcodec == 'none' or vcodec is None) and (acodec != 'none' and acodec is not None)
                
                if is_audio_only:
                    # فرض صيغة m4a أو mp3 لضمان السرعة والتشغيل السليم كموسيقى
                    audio_ext = 'm4a' if ext in ['m4a', 'mp4'] else 'mp3'
                    note = f.get('format_note') or f.get('abr') or 'Standard Audio'
                    
                    available_formats.append({
                        'format_id': f.get('format_id'),
                        'quality': 'audio',
                        'format_note': f"صوت ({note})",
                        'resolution': 'Audio',
                        'ext': audio_ext,
                        'url': f.get('url'),
                        'acodec': acodec,
                        'vcodec': 'none',
                        'filesize': f.get('filesize')
                    })
                elif vcodec != 'none':
                    # صيغ الفيديوهات العادية
                    available_formats.append({
                        'format_id': f.get('format_id'),
                        'quality': f.get('quality'),
                        'format_note': f.get('format_note'),
                        'resolution': f.get('resolution'),
                        'ext': 'mp4' if ext in ['mp4', 'm4v'] else ext,
                        'url': f.get('url'),
                        'acodec': acodec,
                        'vcodec': vcodec,
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
    
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        'outtmpl': filepath,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return send_file(filepath, as_attachment=True, download_name="Boykta_Video.mp4")
    except Exception as e:
        return str(e), 500

@app.route('/', methods=['GET'])
def home():
    return "Boykta Backend is Running on Railway! 🚀"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
