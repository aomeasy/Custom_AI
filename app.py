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

# Default login credentials
DEFAULT_USER = "admin"
DEFAULT_PASSWORD = "password"

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
    """Authenticate user - first check default credentials, then Google Sheets"""
    try:
        # Check default credentials first
        if username == DEFAULT_USER and password == DEFAULT_PASSWORD:
            return True
        
        # Then check Google Sheets
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        if data and len(data) > 1:  # Check if we have data beyond headers
            # Look for user in A2, B2 or scan through the sheet
            for i, row in enumerate(data[1:], 1):  # Skip header row
                if len(row) >= 2 and row[0] == username and row[1] == password:
                    return True
        return False
    except Exception as e:
        print(f"Authentication error: {e}")
        # If Google Sheets fails, still allow default login
        return username == DEFAULT_USER and password == DEFAULT_PASSWORD

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
            'login': f'ข้อมูลการเข้าสู่ระบบ Default: Username: {DEFAULT_USER}, Password: {DEFAULT_PASSWORD}',
            'คู่มือ': f'''คู่มือการใช้งาน Custom AI:

🔐 การเข้าสู่ระบบ:
- Username: {DEFAULT_USER}
- Password: {DEFAULT_PASSWORD}
- หรือใช้ข้อมูลจาก Google Sheet (ถ้ามี)

📝 การเริ่มต้น:
1. เข้าสู่ระบบด้วย admin/password
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
        response = f"ฉันพร้อมช่วยคุณ! ข้อมูลเข้าสู่ระบบ: {DEFAULT_USER}/{DEFAULT_PASSWORD} พิมพ์ 'ช่วย' เพื่อดูคำสั่งที่ใช้ได้ หรือ 'คู่มือ' เพื่อดูคู่มือทั้งหมด"
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
