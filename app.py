import os
from flask import Flask, request, jsonify
import yt_dlp
from waitress import serve

app = Flask(__name__)

@app.route('/api/extract', methods=['POST'])
def extract_video_info():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'لم يتم العثور على رابط (URL) في الطلب'}), 400
    
    video_url = data['url']
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            extracted_formats = []
            for f in info.get('formats', []):
                if f.get('url') and f.get('ext') in ['mp4', 'm4a']:
                    extracted_formats.append({
                        'quality': f.get('format_note', 'Unknown') or f.get('resolution', 'Audio'),
                        'ext': f.get('ext'),
                        'filesize': f.get('filesize', 0),
                        'url': f.get('url')
                    })

            return jsonify({
                'status': 'success',
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'formats': extracted_formats
            }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # رايلواي يحدد المنفذ تلقائياً، هذا السطر يقرأه
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 جاري تشغيل الخادم على المنفذ {port}...")
    serve(app, host='0.0.0.0', port=port)
