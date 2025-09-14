from flask import Flask, render_template, request, jsonify, session
import requests
import json
import os
from datetime import datetime
import re
import codecs
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
    'system_prompt': '''คุณเป็น AI Assistant ที่ช่วยค้นหาข้อมูลจาก Google Sheets อย่างชาญฉลาด ตอบคำถามด้วยความเป็นมิตรและให้ข้อมูลที่ถูกต้อง

คำแนะนำสำคัญ:
- ตอบคำถามเป็นภาษาไทยเท่านั้น
- ไม่แสดงกระบวนการคิดหรือการวิเคราะห์ภายในให้ผู้ใช้เห็น
- ห้ามใช้ภาษาอังกฤษในการตอบ ยกเว้นข้อมูลเฉพาะที่จำเป็น เช่น รหัสหรือเลขที่
- ตอบตรงประเด็นและชัดเจน
- แสดงข้อมูลในรูปแบบที่อ่านง่าย
- หากไม่พบข้อมูลที่ต้องการ ให้แจ้งอย่างสุภาพและเสนอทางเลือก
- ใช้ภาษาที่เป็นมิตรและเหมาะสมสำหรับการใช้งานในองค์กร

ข้อกำหนดพิเศษ:
- ห้ามแสดง tag <think> หรือกระบวนการคิดใดๆ ให้ผู้ใช้เห็น
- ตอบเฉพาะผลลัพธ์สุดท้ายเป็นภาษาไทยเท่านั้น
- หากต้องวิเคราะห์ข้อมูล ให้ทำภายในและแสดงเฉพาะผลลัพธ์
- รักษาความเป็นมืออาชีพในการตอบทุกคำถาม
- จัดรูปแบบข้อมูลให้อ่านง่าย เช่น ใส่หัวข้อ หรือจัดเรียงเป็นรายการ
- หาก Context มีข้อมูล ให้ตอบจากข้อมูลนั้นเสมอ''',
    'google_sheet_id': DEFAULT_SHEET_ID,
    'line_token': '',
    'telegram_api': ''
}


def clean_thai_text(text):
    """แปลง Unicode escape sequences กลับเป็นภาษาไทย"""
    if not text or not isinstance(text, str):
        return text
    
    # ตรวจสอบว่ามี Unicode escape sequences หรือไม่
    if '\\u' not in text:
        return text
    
    try:
        # วิธีที่ 1: ใช้ codecs.decode สำหรับ unicode_escape
        cleaned = codecs.decode(text, 'unicode_escape')
        return cleaned
    except:
        try:
            # วิธีที่ 2: ใช้ encode/decode method
            cleaned = text.encode().decode('unicode_escape')
            return cleaned
        except:
            try:
                # วิธีที่ 3: ใช้ regular expression กับ codecs
                def decode_match(match):
                    return chr(int(match.group(1), 16))
                cleaned = re.sub(r'\\u([0-9a-fA-F]{4})', decode_match, text)
                return cleaned
            except:
                # หากแปลงไม่ได้ทุกวิธี ให้คืนค่าเดิม
                return text
                
def get_google_sheet_data(sheet_id, range_name="A:Z"):
    """Fetch data from Google Sheets with improved error handling and Thai language support"""
    try:
        # Using public Google Sheets CSV export
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        print(f"[DEBUG] Fetching Google Sheet: {csv_url}")
        
        # ปรับปรุง headers เพื่อรองรับ UTF-8
        headers = {
            'Accept': 'text/csv; charset=utf-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(csv_url, headers=headers, timeout=10)
        print(f"[DEBUG] Google Sheets response status: {response.status_code}")
        
        if response.status_code == 200:
            # ตรวจสอบ encoding ของ response
            response.encoding = 'utf-8'
            csv_content = response.text
            
            print(f"[DEBUG] Raw CSV response length: {len(csv_content)} characters")
            print(f"[DEBUG] CSV preview: {csv_content[:200]}...")
            
            # Better CSV parsing using csv module
            csv_data = StringIO(csv_content)
            reader = csv.reader(csv_data)
            data = []
            
            for row_num, row in enumerate(reader):
                # ทำความสะอาดข้อมูลในแต่ละเซลล์เพื่อแปลง Unicode escape sequences
                cleaned_row = []
                for cell in row:
                    if cell:
                        cleaned_cell = clean_thai_text(cell)
                        cleaned_row.append(cleaned_cell)
                    else:
                        cleaned_row.append(cell)
                
                data.append(cleaned_row)
                
                # Debug: แสดง 3 แถวแรกเพื่อตรวจสอบ
                if row_num < 3:
                    print(f"[DEBUG] Row {row_num + 1} (original): {row}")
                    print(f"[DEBUG] Row {row_num + 1} (cleaned): {cleaned_row}")
            
            print(f"[DEBUG] Successfully parsed {len(data)} rows from Google Sheets")
            print(f"[DEBUG] Sample cleaned data: {data[0] if data else 'No data'}")
            
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
    """Search for relevant data in Google Sheets with enhanced pattern matching"""
    try:
        print(f"[DEBUG] Searching Google Sheets for query: '{query}'")
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        
        if not data:
            print("[DEBUG] No data returned from Google Sheets")
            return "ไม่สามารถเข้าถึงข้อมูลได้ในขณะนี้"
        
        print(f"[DEBUG] Searching through {len(data)} rows")
        
        query_lower = query.lower()
        
        # Check for common data viewing patterns
        show_data_patterns = [
            'ขอดูข้อมูล', 'แสดงข้อมูล', 'ดูข้อมูล', 'แสดง', 'ดู',
            'แถวแรก', 'แถว', 'รายการ', 'ข้อมูลทั้งหมด',
            'show data', 'display data', 'view data', 'first rows'
        ]
        
        # Check if user wants to view data
        is_data_request = any(pattern in query_lower for pattern in show_data_patterns)
        
        # Extract number of rows if specified
        import re
        numbers = re.findall(r'\d+', query)
        requested_rows = int(numbers[0]) if numbers else 5
        
        if is_data_request:
            # Return first N rows of data
            print(f"[DEBUG] Detected data viewing request for {requested_rows} rows")
            result_rows = []
            
            # Limit to reasonable number
            max_rows = min(requested_rows, 10, len(data))
            
            for i in range(max_rows):
                if i < len(data) and data[i]:
                    row_display = ' | '.join([str(cell) for cell in data[i] if cell])
                    result_rows.append(f"แถวที่ {i + 1}: {row_display}")
            
            if result_rows:
                result = "\n".join(result_rows)
                print(f"[DEBUG] Returning {len(result_rows)} rows of data")
                return result
            else:
                return "ไม่พบข้อมูลใน Google Sheets"
        
        # Original search functionality for specific content
        relevant_data = []
        
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                if cell and query_lower in str(cell).lower():
                    relevant_data.append(f"แถวที่ {row_idx + 1}: {' | '.join([str(c) for c in row if c])}")
                    print(f"[DEBUG] Match found at row {row_idx + 1}, col {col_idx + 1}: {cell}")
        
        print(f"[DEBUG] Found {len(relevant_data)} matches")
        
        if relevant_data:
            # Remove duplicates and return top 5 matches
            unique_data = list(dict.fromkeys(relevant_data))
            result = "\n".join(unique_data[:5])
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

def filter_ai_response(response):
    """Filter out unwanted content from AI response - Enhanced version"""
    if not response:
        return response
    
    import re
    
    # Remove thinking process tags and content (case insensitive)
    thinking_patterns = [
        r'<think>.*?</think>',
        r'<thinking>.*?</thinking>', 
        r'<analysis>.*?</analysis>',
        r'<reasoning>.*?</reasoning>',
        r'<internal>.*?</internal>',
        r'<thought>.*?</thought>',
        r'\*thinking\*.*?\*thinking\*',
        r'\[thinking\].*?\[/thinking\]',
        r'\(thinking:.*?\)',
        r'<พิจารณา>.*?</พิจารณา>',
        r'<คิด>.*?</คิด>'
    ]
    
    for pattern in thinking_patterns:
        response = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove common English thinking phrases at the beginning
    english_patterns = [
        r'^Looking at.*?(?=\n|\.|$)',
        r'^Based on.*?(?=\n|\.|$)', 
        r'^From the.*?(?=\n|\.|$)',
        r'^In the.*?(?=\n|\.|$)',
        r'^The user.*?(?=\n|\.|$)',
        r'^I can see.*?(?=\n|\.|$)',
        r'^According to.*?(?=\n|\.|$)',
        r'^Analyzing.*?(?=\n|\.|$)'
    ]
    
    for pattern in english_patterns:
        response = re.sub(pattern, '', response, flags=re.MULTILINE | re.IGNORECASE)
    
    # Split response and keep only Thai content parts
    lines = response.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines that are predominantly English (rough check)
        thai_chars = len(re.findall(r'[ก-๙]', line))
        english_chars = len(re.findall(r'[a-zA-Z]', line))
        
        # Keep line if it has Thai content or essential data
        if (thai_chars > 0 or 
            any(keyword in line for keyword in ['SD', ':', '-', '**', '•', '1.', '2.']) or
            re.match(r'^\d+', line) or  # Lines starting with numbers
            len(line) < 50):  # Short lines might be data
            filtered_lines.append(line)
    
    # Reconstruct response
    response = '\n'.join(filtered_lines)
    
    # Clean up multiple newlines and spaces
    response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
    response = re.sub(r'^\s+|\s+$', '', response)
    
    # Ensure the response starts properly (remove any leftover English intro)
    if response:
        first_line = response.split('\n')[0]
        if (len(re.findall(r'[a-zA-Z]', first_line)) > len(re.findall(r'[ก-๙]', first_line)) and
            len(first_line) > 30):
            # Remove first line if it's predominantly English
            response = '\n'.join(response.split('\n')[1:])
    
    # Ensure the response is not empty
    if not response or response.isspace():
        return "ขออภัย ไม่สามารถประมวลผลคำตอบได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง"
    
    return response.strip()

def call_ai_model(prompt, context=""):
    """Call the AI model with context and enhanced debugging"""
    try:
        # Enhanced system prompt to handle data viewing requests better
        enhanced_system_prompt = f"""{app_settings['system_prompt']}

คำแนะนำเพิ่มเติม:
- ห้ามแสดงกระบวนการคิด (thinking process) หรือ internal analysis
- ห้ามใช้ tag <think> หรือแท็กคล้ายๆ ในการตอบ
- ตอบเป็นภาษาไทยเท่านั้น
- เมื่อผู้ใช้ถามขอดูข้อมูล แสดงข้อมูล หรือคำถามคล้ายกัน ให้แสดงข้อมูลที่มีใน Context
- หากมีข้อมูลใน Context แล้ว ไม่ต้องบอกว่า "ไม่พบข้อมูล"
- จัดรูปแบบข้อมูลให้อ่านง่าย เช่น ใส่หัวข้อ หรือจัดเรียงเป็นตาราง
- หาก Context มีข้อมูล ให้ตอบจากข้อมูลนั้นเสมอ"""
        
        full_prompt = f"{enhanced_system_prompt}\n\nContext from Google Sheets:\n{context}\n\nUser question: {prompt}"
        
        payload = {
            "model": CHAT_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "temperature": 0.1,  # Very low temperature for consistent output
            "top_p": 0.7,        # More focused responses
            "max_tokens": 600    # Limit response length
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

# New endpoint for directly viewing sheet data (for debugging)
@app.route('/api/preview-data', methods=['POST'])
def preview_data():
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        num_rows = data.get('rows', 5)
        
        sheet_data = get_google_sheet_data(app_settings['google_sheet_id'])
        
        if not sheet_data:
            return jsonify({
                'success': False,
                'error': 'ไม่สามารถเข้าถึง Google Sheet ได้'
            })
        
        preview_rows = []
        for i, row in enumerate(sheet_data[:num_rows]):
            preview_rows.append({
                'row_number': i + 1,
                'data': row,
                'display': f"แถวที่ {i+1}: {' | '.join(str(cell) for cell in row) if row else '(ว่าง)'}"
            })
        
        return jsonify({
            'success': True,
            'total_rows': len(sheet_data),
            'preview_rows': len(preview_rows),
            'data': preview_rows,
            'sheet_id': app_settings['google_sheet_id'],
            'raw_sample': sheet_data[:3] if sheet_data else []
        })
        
    except Exception as e:
        print(f"[DEBUG] Preview data error: {e}")
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        })
        
    
    # แปลง Unicode escape sequences
    try:
        # วิธีที่ 1: ใช้ codecs.decode
        cleaned = codecs.decode(text, 'unicode_escape')
        return cleaned
    except:
        try:
            # วิธีที่ 2: ใช้ encode/decode
            cleaned = text.encode().decode('unicode_escape')
            return cleaned
        except:
            # หากแปลงไม่ได้ ให้คืนค่าเดิม
            return text

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
