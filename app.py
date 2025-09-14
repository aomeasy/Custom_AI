from flask import Flask, render_template, request, jsonify, session
import requests
import json
import os
from datetime import datetime
import re
import csv
from io import StringIO

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
    """Fetch data from Google Sheets with improved error handling"""
    try:
        # Using public Google Sheets CSV export
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        print(f"[DEBUG] Fetching Google Sheet: {csv_url}")
        
        response = requests.get(csv_url, timeout=10)
        print(f"[DEBUG] Google Sheets response status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"[DEBUG] Raw CSV response length: {len(response.text)} characters")
            print(f"[DEBUG] CSV preview: {response.text[:200]}...")
            
            # Better CSV parsing using csv module
            csv_data = StringIO(response.text)
            reader = csv.reader(csv_data)
            data = []
            
            for row_num, row in enumerate(reader):
                data.append(row)
                if row_num < 3:  # Show first 3 rows for debugging
                    print(f"[DEBUG] Row {row_num + 1}: {row}")
            
            print(f"[DEBUG] Successfully parsed {len(data)} rows from Google Sheets")
            return data
        else:
            print(f"[DEBUG] Google Sheets error: HTTP {response.status_code}")
            print(f"[DEBUG] Error response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"[DEBUG] Error fetching Google Sheets data: {e}")
        import traceback
        traceback.print_exc()
        return None

def authenticate_user(username, password):
    """Authenticate user - first check default credentials, then Google Sheets"""
    try:
        # Check default credentials first
        if username == DEFAULT_USER and password == DEFAULT_PASSWORD:
            print(f"[DEBUG] User authenticated with default credentials: {username}")
            return True
        
        # Then check Google Sheets
        print(f"[DEBUG] Checking Google Sheets for user: {username}")
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        if data and len(data) > 1:  # Check if we have data beyond headers
            print(f"[DEBUG] Searching through {len(data)} rows for user credentials")
            # Look for user in A2, B2 or scan through the sheet
            for i, row in enumerate(data[1:], 1):  # Skip header row
                if len(row) >= 2 and row[0] == username and row[1] == password:
                    print(f"[DEBUG] User found in Google Sheets at row {i + 1}")
                    return True
        
        print(f"[DEBUG] User authentication failed: {username}")
        return False
    except Exception as e:
        print(f"[DEBUG] Authentication error: {e}")
        # If Google Sheets fails, still allow default login
        return username == DEFAULT_USER and password == DEFAULT_PASSWORD

def search_sheet_data(query):
    """Search for relevant data in Google Sheets with enhanced debugging"""
    try:
        print(f"[DEBUG] Searching Google Sheets for query: '{query}'")
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        
        if not data:
            print("[DEBUG] No data returned from Google Sheets")
            return "ไม่สามารถเข้าถึงข้อมูลได้ในขณะนี้"
        
        print(f"[DEBUG] Searching through {len(data)} rows")
        
        # Simple search through all cells
        relevant_data = []
        query_lower = query.lower()
        
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                if cell and query_lower in cell.lower():
                    relevant_data.append(f"แถวที่ {row_idx + 1}: {' | '.join(row)}")
                    print(f"[DEBUG] Match found at row {row_idx + 1}, col {col_idx + 1}: {cell}")
        
        print(f"[DEBUG] Found {len(relevant_data)} matches")
        
        if relevant_data:
            result = "\n".join(relevant_data[:5])  # Return top 5 matches
            print(f"[DEBUG] Returning search results: {result[:200]}...")
            return result
        else:
            print("[DEBUG] No matches found in search")
            return "ไม่พบข้อมูลที่ตรงกับคำค้นหา"
            
    except Exception as e:
        print(f"[DEBUG] Search error: {e}")
        import traceback
        traceback.print_exc()
        return f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"

def call_ai_model(prompt, context=""):
    """Call the AI model with context and enhanced debugging"""
    try:
        full_prompt = f"{app_settings['system_prompt']}\n\nContext from Google Sheets:\n{context}\n\nUser question: {prompt}"
        
        payload = {
            "model": CHAT_MODEL,
            "prompt": full_prompt,
            "stream": False
        }
        
        print(f"[DEBUG] Calling AI model: {CHAT_MODEL}")
        print(f"[DEBUG] API URL: {CHAT_API_URL}")
        print(f"[DEBUG] Prompt length: {len(full_prompt)} characters")
        print(f"[DEBUG] Context preview: {context[:200]}...")
        
        response = requests.post(CHAT_API_URL, json=payload, timeout=30)
        
        print(f"[DEBUG] AI response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', 'ไม่สามารถสร้างคำตอบได้')
            print(f"[DEBUG] AI response length: {len(ai_response)} characters")
            print(f"[DEBUG] AI response preview: {ai_response[:200]}...")
            return ai_response
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            print(f"[DEBUG] AI error: {error_msg}")
            return "ขออภัย เกิดข้อผิดพลาดในการเชื่อมต่อ AI"
            
    except Exception as e:
        print(f"[DEBUG] AI Model error: {e}")
        import traceback
        traceback.print_exc()
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
        
        print(f"[DEBUG] Login attempt for user: {username}")
        
        if authenticate_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            print(f"[DEBUG] Login successful for user: {username}")
            return jsonify({'success': True, 'message': 'เข้าสู่ระบบสำเร็จ'})
        else:
            print(f"[DEBUG] Login failed for user: {username}")
            return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'})
            
    except Exception as e:
        print(f"[DEBUG] Login error: {e}")
        return jsonify({'success': False, 'message': 'เกิดข้อผิดพลาดในระบบ'})

@app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username', 'unknown')
    session.clear()
    print(f"[DEBUG] User logged out: {username}")
    return jsonify({'success': True, 'message': 'ออกจากระบบสำเร็จ'})

@app.route('/api/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        message = data.get('message', '')
        
        print(f"[DEBUG] Chat message received: '{message}'")
        
        if not message:
            return jsonify({'error': 'กรุณาใส่ข้อความ'})
        
        # Search for relevant context in Google Sheets
        print("[DEBUG] Starting Google Sheets search...")
        context = search_sheet_data(message)
        
        # Get AI response
        print("[DEBUG] Starting AI model call...")
        ai_response = call_ai_model(message, context)
        
        context_found = bool(context and 'ไม่พบข้อมูล' not in context and 'ไม่สามารถเข้าถึงข้อมูล' not in context)
        
        print(f"[DEBUG] Chat response completed - Context found: {context_found}")
        
        return jsonify({
            'response': ai_response,
            'context_found': context_found,
            'timestamp': datetime.now().isoformat(),
            'debug_info': {
                'context_preview': context[:100] + '...' if len(context) > 100 else context,
                'sheet_id': app_settings['google_sheet_id']
            }
        })
        
    except Exception as e:
        print(f"[DEBUG] Chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'เกิดข้อผิดพลาดในการประมวลผล'}), 500

@app.route('/api/admin-help', methods=['POST'])
def admin_help():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        question = data.get('message', '')
        
        print(f"[DEBUG] Admin help request: '{question}'")
        
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
        print(f"[DEBUG] Admin help error: {e}")
        return jsonify({'error': 'เกิดข้อผิดพลาดในระบบช่วยเหลือ'}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    if request.method == 'POST':
        try:
            data = request.json
            old_sheet_id = app_settings['google_sheet_id']
            
            app_settings.update({
                'system_prompt': data.get('system_prompt', app_settings['system_prompt']),
                'google_sheet_id': data.get('google_sheet_id', app_settings['google_sheet_id']),
                'line_token': data.get('line_token', app_settings['line_token']),
                'telegram_api': data.get('telegram_api', app_settings['telegram_api'])
            })
            
            print(f"[DEBUG] Settings updated - Sheet ID changed from {old_sheet_id} to {app_settings['google_sheet_id']}")
            
            return jsonify({'success': True, 'message': 'บันทึกการตั้งค่าสำเร็จ'})
        except Exception as e:
            print(f"[DEBUG] Settings update error: {e}")
            return jsonify({'success': False, 'message': 'เกิดข้อผิดพลาดในการบันทึก'})
    
    return jsonify(app_settings)

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        print("[DEBUG] Starting connection test...")
        
        # Test Google Sheets connection
        print("[DEBUG] Testing Google Sheets connection...")
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        sheets_status = bool(data)
        sheets_details = f"Found {len(data)} rows" if data else "No data accessible"
        
        # Test AI model connection
        print("[DEBUG] Testing AI model connection...")
        try:
            test_response = requests.post(CHAT_API_URL, 
                                        json={"model": CHAT_MODEL, "prompt": "test", "stream": False}, 
                                        timeout=10)
            ai_status = test_response.status_code == 200
            ai_details = f"HTTP {test_response.status_code}"
            if test_response.status_code == 200:
                ai_result = test_response.json()
                ai_details += f" - Response: {ai_result.get('response', 'No response')[:50]}..."
        except Exception as e:
            ai_status = False
            ai_details = f"Error: {str(e)}"
        
        result = {
            'google_sheets': sheets_status,
            'google_sheets_details': sheets_details,
            'ai_model': ai_status,
            'ai_model_details': ai_details,
            'message': f"Google Sheets: {'✅ ' + sheets_details if sheets_status else '❌ ' + sheets_details}, AI Model: {'✅ ' + ai_details if ai_status else '❌ ' + ai_details}",
            'debug_info': {
                'sheet_id': app_settings['google_sheet_id'],
                'sheet_url': f"https://docs.google.com/spreadsheets/d/{app_settings['google_sheet_id']}/export?format=csv&gid=0",
                'ai_model': CHAT_MODEL,
                'ai_url': CHAT_API_URL
            }
        }
        
        print(f"[DEBUG] Connection test completed: Sheets={sheets_status}, AI={ai_status}")
        return jsonify(result)
        
    except Exception as e:
        print(f"[DEBUG] Connection test error: {e}")
        return jsonify({'error': f'เกิดข้อผิดพลาดในการทดสอบ: {str(e)}'}), 500

# New endpoint for detailed Google Sheets testing
@app.route('/api/test-sheet', methods=['POST'])
def test_sheet():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    sheet_id = app_settings['google_sheet_id']
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    print(f"[DEBUG] Testing Google Sheet access: {sheet_id}")
    
    try:
        response = requests.get(csv_url, timeout=10)
        
        result = {
            'sheet_id': sheet_id,
            'url': csv_url,
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'content_length': len(response.text) if response.status_code == 200 else 0,
            'content_preview': response.text[:500] if response.status_code == 200 else None,
            'error': None if response.status_code == 200 else f"HTTP {response.status_code}: {response.text[:200]}"
        }
        
        if response.status_code == 200:
            # Try to parse the CSV
            try:
                csv_data = StringIO(response.text)
                reader = csv.reader(csv_data)
                rows = list(reader)
                result['parsed_rows'] = len(rows)
                result['sample_data'] = rows[:3] if rows else []
            except Exception as parse_error:
                result['parse_error'] = str(parse_error)
        
        print(f"[DEBUG] Sheet test result: {result['success']}")
        return jsonify(result)
        
    except Exception as e:
        print(f"[DEBUG] Sheet test error: {e}")
        return jsonify({
            'sheet_id': sheet_id,
            'url': csv_url,
            'success': False,
            'error': str(e)
        })

# New endpoint for testing Unicode conversion
@app.route('/api/test-unicode', methods=['POST'])
def test_unicode():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        test_text = data.get('text', 'à¸à¸²à¸£à¹à¸à¹à¸à¸£à¸²à¸°')
        
        original = test_text
        cleaned = clean_thai_text(test_text)
        
        # Test different decoding methods
        methods = {}
        
        try:
            methods['unicode_escape'] = test_text.encode().decode('unicode_escape')
        except:
            methods['unicode_escape'] = 'Failed'
            
        try:
            methods['codecs_decode'] = codecs.decode(test_text, 'unicode_escape')
        except:
            methods['codecs_decode'] = 'Failed'
            
        try:
            methods['utf8_decode'] = test_text.encode('latin1').decode('utf-8')
        except:
            methods['utf8_decode'] = 'Failed'
        
        return jsonify({
            'original': original,
            'cleaned': cleaned,
            'methods': methods,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'})

# New endpoint for testing search functionality
@app.route('/api/test-search', methods=['POST'])
def test_search():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'กรุณาใส่คำค้นหา'})
        
        print(f"[DEBUG] Test search for: '{query}'")
        
        # Get raw sheet data
        sheet_data = get_google_sheet_data(app_settings['google_sheet_id'])
        
        # Perform search
        search_result = search_sheet_data(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'sheet_rows': len(sheet_data) if sheet_data else 0,
            'search_result': search_result,
            'sheet_preview': sheet_data[:3] if sheet_data else [],
            'sheet_id': app_settings['google_sheet_id']
        })
        
    except Exception as e:
        print(f"[DEBUG] Test search error: {e}")
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'})

# New endpoint for viewing sheet data
@app.route('/api/view-sheet', methods=['POST'])
def view_sheet():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        
        if not data:
            return jsonify({'error': 'ไม่สามารถเข้าถึง Google Sheet ได้'})
        
        # Return first 10 rows for inspection
        preview_data = []
        for i, row in enumerate(data[:10]):
            preview_data.append({
                'row_number': i + 1,
                'data': row,
                'joined': ' | '.join(row) if row else ''
            })
        
        return jsonify({
            'success': True,
            'total_rows': len(data),
            'preview_rows': len(preview_data),
            'data': preview_data,
            'headers': data[0] if data else [],
            'sheet_id': app_settings['google_sheet_id']
        })
        
    except Exception as e:
        print(f"[DEBUG] View sheet error: {e}")
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'})

if __name__ == '__main__':
    print("[DEBUG] Starting Flask application...")
    print(f"[DEBUG] Default Google Sheet ID: {DEFAULT_SHEET_ID}")
    print(f"[DEBUG] AI Model: {CHAT_MODEL}")
    print(f"[DEBUG] AI API URL: {CHAT_API_URL}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
