from flask import Flask, render_template, request, jsonify, session
import requests
import json
import os
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configuration
CHAT_API_URL = "http://209.15.123.47:11434/api/generate"
CHAT_MODEL = "Qwen3:14b"
DEFAULT_SHEET_ID = "1_YcWW9AWew9afLVk08Tl5lN4iQMhxiQDz4qU3LsB-iE"

# In-memory storage (for demo purposes - in production use database)
app_settings = {
    'system_prompt': 'คุณเป็น AI Assistant ที่ช่วยค้นหาข้อมูลจาก Google Sheets อย่างชาญฉลาด ตอบคำถามด้วยความเป็นมิตรและให้ข้อมูลที่ถูกต้อง',
    'google_sheet_id': DEFAULT_SHEET_ID,
    'line_token': '',
    'telegram_api': ''
}

def get_google_sheet_data(sheet_id, range_name="A:Z"):
    """Fetch data from Google Sheets"""
    try:
        # Using public Google Sheets CSV export
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        response = requests.get(csv_url, timeout=10)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            data = []
            for line in lines:
                row = [cell.strip('"') for cell in line.split(',')]
                data.append(row)
            return data
        return None
    except Exception as e:
        print(f"Error fetching Google Sheets data: {e}")
        return None

def authenticate_user(username, password):
    """Authenticate user against Google Sheets"""
    try:
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        if data and len(data) > 1:  # Check if we have data beyond headers
            # Look for user in A2, B2 or scan through the sheet
            for i, row in enumerate(data[1:], 1):  # Skip header row
                if len(row) >= 2 and row[0] == username and row[1] == password:
                    return True
        return False
    except Exception as e:
        print(f"Authentication error: {e}")
        return False

def search_sheet_data(query):
    """Search for relevant data in Google Sheets"""
    try:
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        if not data:
            return "ไม่สามารถเข้าถึงข้อมูลได้ในขณะนี้"
        
        # Simple search through all cells
        relevant_data = []
        query_lower = query.lower()
        
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                if cell and query_lower in cell.lower():
                    relevant_data.append(f"แถวที่ {row_idx + 1}: {' | '.join(row)}")
        
        if relevant_data:
            return "\n".join(relevant_data[:5])  # Return top 5 matches
        else:
            return "ไม่พบข้อมูลที่ตรงกับคำค้นหา"
            
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"

def call_ai_model(prompt, context=""):
    """Call the AI model with context"""
    try:
        full_prompt = f"{app_settings['system_prompt']}\n\nContext from Google Sheets:\n{context}\n\nUser question: {prompt}"
        
        payload = {
            "model": CHAT_MODEL,
            "prompt": full_prompt,
            "stream": False
        }
        
        response = requests.post(CHAT_API_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'ไม่สามารถสร้างคำตอบได้')
        else:
            return "ขออภัย เกิดข้อผิดพลาดในการเชื่อมต่อ AI"
            
    except Exception as e:
        print(f"AI Model error: {e}")
        return "เกิดข้อผิดพลาดในการประมวลผล โปรดลองใหม่อีกครั้ง"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if authenticate_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return jsonify({'success': True, 'message': 'เข้าสู่ระบบสำเร็จ'})
        else:
            return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'เกิดข้อผิดพลาดในระบบ'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'ออกจากระบบสำเร็จ'})

@app.route('/api/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'กรุณาใส่ข้อความ'})
        
        # Search for relevant context in Google Sheets
        context = search_sheet_data(message)
        
        # Get AI response
        ai_response = call_ai_model(message, context)
        
        return jsonify({
            'response': ai_response,
            'context_found': bool(context and 'ไม่พบข้อมูล' not in context),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': 'เกิดข้อผิดพลาดในการประมวลผล'}), 500

@app.route('/api/admin-help', methods=['POST'])
def admin_help():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        question = data.get('message', '')
        
        # Admin helper responses
        help_responses = {
            'การตั้งค่า': 'สำหรับการตั้งค่าระบบ: 1. ไปที่หน้า Settings 2. ใส่ System Prompt ที่ต้องการ 3. ใส่ Google Sheet ID 4. บันทึกการตั้งค่า',
            'google sheet': 'การใช้งาน Google Sheets: 1. เตรียม Google Sheet ที่เป็น Public 2. คัดลอก Sheet ID จาก URL 3. ใส่ใน Settings 4. ทดสอบการค้นหา',
            'ช่วย': 'คุณสามารถถามเกี่ยวกับ: การตั้งค่าระบบ, การใช้งาน Google Sheets, การใช้งาน Chatbot, การแก้ไขปัญหา, หรือพิมพ์ "คู่มือ" เพื่อดูคู่มือทั้งหมด',
            'คู่มือ': '''คู่มือการใช้งาน Custom AI:

📝 การเริ่มต้น:
1. เข้าสู่ระบบด้วย user/password จาก Google Sheet
2. ตั้งค่า System Prompt และ Google Sheet ID
3. ทดสอบการทำงานของ Chatbot

⚙️ การตั้งค่า:
- System Prompt: คำสั่งให้ AI ทำงาน
- Google Sheet ID: รหัส Google Sheet สำหรับค้นหาข้อมูล
- API Tokens: สำหรับ Line/Telegram (ถ้ามี)

💬 การใช้งาน Chat:
- พิมพ์คำถามเพื่อค้นหาข้อมูลใน Google Sheet
- AI จะค้นหาและตอบคำถามจากข้อมูลที่เจอ
- สามารถถามได้หลากหลายรูปแบบ'''
        }
        
        # Find best matching response
        question_lower = question.lower()
        response = "ฉันพร้อมช่วยคุณ! พิมพ์ 'ช่วย' เพื่อดูคำสั่งที่ใช้ได้ หรือ 'คู่มือ' เพื่อดูคู่มือทั้งหมด"
        
        for key, value in help_responses.items():
            if key in question_lower:
                response = value
                break
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': 'เกิดข้อผิดพลาดในระบบช่วยเหลือ'}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    if request.method == 'POST':
        try:
            data = request.json
            app_settings.update({
                'system_prompt': data.get('system_prompt', app_settings['system_prompt']),
                'google_sheet_id': data.get('google_sheet_id', app_settings['google_sheet_id']),
                'line_token': data.get('line_token', app_settings['line_token']),
                'telegram_api': data.get('telegram_api', app_settings['telegram_api'])
            })
            return jsonify({'success': True, 'message': 'บันทึกการตั้งค่าสำเร็จ'})
        except Exception as e:
            return jsonify({'success': False, 'message': 'เกิดข้อผิดพลาดในการบันทึก'})
    
    return jsonify(app_settings)

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        # Test Google Sheets connection
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        sheets_status = bool(data)
        
        # Test AI model connection
        test_response = requests.post(CHAT_API_URL, 
                                    json={"model": CHAT_MODEL, "prompt": "test", "stream": False}, 
                                    timeout=10)
        ai_status = test_response.status_code == 200
        
        return jsonify({
            'google_sheets': sheets_status,
            'ai_model': ai_status,
            'message': f"Google Sheets: {'✅' if sheets_status else '❌'}, AI Model: {'✅' if ai_status else '❌'}"
        })
        
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาดในการทดสอบ: {str(e)}'}), 500

# LINE Webhook
@app.route('/webhook/line', methods=['POST'])
def line_webhook():
    """Handle LINE webhook messages"""
    try:
        # Get request data
        body = request.get_json()
        
        # Validate LINE signature (optional - for production security)
        # You can add LINE signature validation here if needed
        
        if not body or 'events' not in body:
            return 'OK', 200
        
        for event in body['events']:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                reply_token = event['replyToken']
                user_message = event['message']['text']
                user_id = event['source']['userId']
                
                # Process message through RAG system
                context = search_sheet_data(user_message)
                ai_response = call_ai_model(user_message, context)
                
                # Send reply back to LINE
                send_line_reply(reply_token, ai_response)
                
        return 'OK', 200
        
    except Exception as e:
        print(f"LINE webhook error: {e}")
        return 'Error', 500

def send_line_reply(reply_token, message):
    """Send reply message to LINE"""
    try:
        line_token = app_settings.get('line_token')
        if not line_token:
            print("LINE token not configured")
            return
            
        url = 'https://api.line.me/v2/bot/message/reply'
        headers = {
            'Authorization': f'Bearer {line_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'replyToken': reply_token,
            'messages': [{
                'type': 'text',
                'text': message[:2000]  # LINE message limit
            }]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send LINE reply: {response.text}")
            
    except Exception as e:
        print(f"Error sending LINE reply: {e}")

# Telegram Webhook
@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """Handle Telegram webhook messages"""
    try:
        # Get request data
        update = request.get_json()
        
        if not update or 'message' not in update:
            return 'OK', 200
            
        message = update['message']
        
        if 'text' in message:
            chat_id = message['chat']['id']
            user_message = message['text']
            
            # Skip commands for now (you can implement commands later)
            if user_message.startswith('/'):
                if user_message == '/start':
                    send_telegram_message(chat_id, "สวัสดี! ฉันเป็น AI Assistant พร้อมช่วยคุณค้นหาข้อมูลจาก Google Sheets")
                return 'OK', 200
            
            # Process message through RAG system
            context = search_sheet_data(user_message)
            ai_response = call_ai_model(user_message, context)
            
            # Send reply back to Telegram
            send_telegram_message(chat_id, ai_response)
            
        return 'OK', 200
        
    except Exception as e:
        print(f"Telegram webhook error: {e}")
        return 'Error', 500

def send_telegram_message(chat_id, message):
    """Send message to Telegram"""
    try:
        telegram_token = app_settings.get('telegram_api')
        if not telegram_token:
            print("Telegram token not configured")
            return
            
        url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': message[:4096],  # Telegram message limit
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=data, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send Telegram message: {response.text}")
            
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# Webhook setup endpoints
@app.route('/api/setup-line-webhook', methods=['POST'])
def setup_line_webhook():
    """Setup LINE webhook URL"""
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        webhook_url = data.get('webhook_url')  # Your Render app URL + /webhook/line
        line_token = app_settings.get('line_token')
        
        if not line_token:
            return jsonify({'error': 'กรุณาตั้งค่า LINE Token ก่อน'}), 400
            
        # Note: LINE webhook setup is usually done through LINE Developer Console
        # This endpoint is for reference/testing purposes
        
        return jsonify({
            'success': True, 
            'message': f'LINE Webhook URL: {webhook_url}',
            'note': 'กรุณาตั้งค่า URL นี้ใน LINE Developer Console'
        })
        
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

@app.route('/api/setup-telegram-webhook', methods=['POST'])
def setup_telegram_webhook():
    """Setup Telegram webhook URL"""
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        webhook_url = data.get('webhook_url')  # Your Render app URL + /webhook/telegram
        telegram_token = app_settings.get('telegram_api')
        
        if not telegram_token:
            return jsonify({'error': 'กรุณาตั้งค่า Telegram API Token ก่อน'}), 400
        
        # Set Telegram webhook
        url = f'https://api.telegram.org/bot{telegram_token}/setWebhook'
        response = requests.post(url, json={'url': webhook_url}, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return jsonify({'success': True, 'message': 'ตั้งค่า Telegram Webhook สำเร็จ'})
            else:
                return jsonify({'error': f'Telegram API Error: {result.get("description", "Unknown error")}'})
        else:
            return jsonify({'error': 'ไม่สามารถเชื่อมต่อ Telegram API ได้'})
            
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

# Test webhook endpoints
@app.route('/api/test-line', methods=['POST'])
def test_line():
    """Test LINE integration"""
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        line_token = app_settings.get('line_token')
        if not line_token:
            return jsonify({'error': 'กรุณาตั้งค่า LINE Token ก่อน'}), 400
        
        # Test LINE API connection
        url = 'https://api.line.me/v2/bot/info'
        headers = {'Authorization': f'Bearer {line_token}'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            return jsonify({
                'success': True, 
                'message': 'เชื่อมต่อ LINE API สำเร็จ',
                'bot_info': bot_info
            })
        else:
            return jsonify({'error': 'LINE Token ไม่ถูกต้อง'})
            
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

@app.route('/api/test-telegram', methods=['POST'])
def test_telegram():
    """Test Telegram integration"""
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        telegram_token = app_settings.get('telegram_api')
        if not telegram_token:
            return jsonify({'error': 'กรุณาตั้งค่า Telegram API Token ก่อน'}), 400
        
        # Test Telegram API connection
        url = f'https://api.telegram.org/bot{telegram_token}/getMe'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result')
                return jsonify({
                    'success': True, 
                    'message': 'เชื่อมต่อ Telegram API สำเร็จ',
                    'bot_info': bot_info
                })
            else:
                return jsonify({'error': 'Telegram API Error'})
        else:
            return jsonify({'error': 'Telegram Token ไม่ถูกต้อง'})
            
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
