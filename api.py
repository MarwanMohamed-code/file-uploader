import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import io

# =======================================================
# ⚠️ 1. إعدادات Telegram API - سيتم جلبها من البيئة ⚠️
# =======================================================
# سيتم استبدال هذه القيم بـ 'True Token' عند النشر
BOT_TOKEN = os.environ.get("BOT_TOKEN", "FAKE_TOKEN") 
CHAT_ID = os.environ.get("CHAT_ID", "-1001234567890") 
# =======================================================

app = Flask(__name__)
# رفع الحد الأقصى لـ 2048 ميجابايت (2 جيجا بايت)
app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024 
CORS(app)

@app.route('/upload_file', methods=['POST'])
def upload_file_to_telegram():
    if not BOT_TOKEN or BOT_TOKEN == "FAKE_TOKEN":
        return jsonify({"success": False, "message": "Server Error: BOT_TOKEN is not configured."})

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file part in the request."})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file."})

    try:
        # 1. نقطة نهاية إرسال المستند
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

        # 2. إرسال الملف إلى Telegram
        files = {
            'document': (file.filename, file.read(), file.mimetype)
        }
        
        payload = {
            'chat_id': CHAT_ID,
            'caption': f"Uploaded via Web App: {file.filename}"
        }

        response = requests.post(telegram_url, data=payload, files=files)
        response.raise_for_status()
        
        data = response.json()
        
        if data['ok']:
            document_info = data['result']['document']
            file_id = document_info['file_id']
            
            # 3. الحصول على رابط التحميل المباشر (رابط مؤقت)
            get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
            file_response = requests.get(get_file_url).json()
            
            if file_response['ok']:
                file_path = file_response['result']['file_path']
                # الرابط النهائي لتحميل الملف (مؤقت)
                download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                
                return jsonify({
                    "success": True, 
                    "url": download_url, 
                    "message": "File uploaded and temporary URL generated."
                })
            else:
                return jsonify({"success": False, "message": f"Failed to get file path: {file_response.get('description', 'Unknown error')}"})

        else:
            return jsonify({"success": False, "message": f"Telegram API Error: {data.get('description', 'Unknown error')}"})

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": f"HTTP Request Failed: {e}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"An unexpected server error occurred: {e}"})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask server on port {port}...")
    # يتم تعطيل Debug=True عند النشر على السيرفرات السحابية
    app.run(host='0.0.0.0', port=port, debug=False)
