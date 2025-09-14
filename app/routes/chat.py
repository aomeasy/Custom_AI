from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.ai_service import AIService
from app.services.rag_engine import RAGEngine

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def chat_page():
    return render_template('chat.html')

@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'ไม่พบข้อความ'}), 400
        
        # Initialize services
        rag_engine = RAGEngine()
        ai_service = AIService()
        
        # Get context from RAG
        context = rag_engine.get_context_for_query(message)
        
        # Generate AI response
        response = ai_service.generate_response(message, context)
        
        return jsonify({
            'success': True,
            'response': response,
            'context_found': bool(context and context != "ไม่พบข้อมูลที่เกี่ยวข้องในระบบ")
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': 'เกิดข้อผิดพลาดในการประมวลผล'}), 500

@chat_bp.route('/admin-help', methods=['POST'])
@login_required
def admin_help():
    """Admin chatbot for helping users"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip().lower()
        
        # Predefined responses for common questions
        responses = {
            'การตั้งค่า': """🔧 **ขั้นตอนการตั้งค่าระบบ:**
            
1. **ไปที่หน้า Settings** 
   - คลิก "Settings" ในเมนู

2. **ตั้งค่า Google Sheets**
   - ใส่ Google Sheets ID
   - อัพโหลด Google Credentials JSON

3. **ตั้งค่า AI**
   - ปรับ System Prompt ตามต้องการ
   - ตั้งค่า AI API URL และ Model

4. **ตั้งค่าการแจ้งเตือน**
   - ใส่ Line Token
   - ใส่ Telegram Bot Token

💡 **เสร็จแล้วอย่าลืมกด "บันทึกการตั้งค่า"**""",
            
            'การใช้งาน': """💬 **วิธีใช้งาน AI Chat:**

1. **พิมพ์คำถาม** - ถามอะไรก็ได้เกี่ยวกับข้อมูลใน Google Sheets
2. **รอการตอบ** - AI จะค้นหาและวิเคราะห์ข้อมูลให้
3. **ดูผลลัพธ์** - ได้คำตอบที่อ้างอิงจากข้อมูลจริง

**ตัวอย่างคำถาม:**
- "ข้อมูลลูกค้าใหม่มีอะไรบ้าง"
- "สรุปยอดขายเดือนนี้"
- "รายชื่อสินค้าที่มีสต็อกน้อย"

🎯 **ยิ่งถามชัดเจน ยิ่งได้คำตอบตรงจุด!**""",
            
            'ปัญหา': """🚨 **แก้ไขปัญหาพบบ่อย:**

**ไม่สามารถล็อกอินได้:**
- ตรวจสอบ username/password ใน Google Sheets ชีต1 cell A2:B2
- ให้แน่ใจว่า Google Sheets เปิดการเข้าถึงได้

**AI ตอบไม่ถูก:**
- ตรวจสอบการตั้งค่า Google Credentials
- ลองรีเฟรชข้อมูล
- ตรวจสอบ AI API URL

**ข้อมูลไม่อัพเดท:**
- กด "รีเฟรชข้อมูล" ในหน้าแชท
- ตรวจสอบว่า Google Sheets มีการเปลี่ยนแปลง

❓ **ยังมีปัญหา? ลองดูใน Settings > ทดสอบการเชื่อมต่อ**""",
            
            'คำถามตัวอย่าง': """💡 **คำถามตัวอย่างที่ดี:**

**สำหรับข้อมูลลูกค้า:**
- "ลูกค้าที่มีอายุมากกว่า 30 ปีมีกี่คน"
- "ลูกค้าจากจังหวัดไหนมีมากที่สุด"
- "ข้อมูลติดต่อของลูกค้าชื่อ..."

**สำหรับข้อมูลสินค้า:**
- "สินค้าใหม่ที่เพิ่งเข้ามามีอะไรบ้าง"
- "ราคาสินค้า... เท่าไหร่"
- "สินค้าหมดสต็อกมีอะไร
