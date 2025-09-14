import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Settings
    CHAT_API_URL = os.environ.get('CHAT_API_URL') or 'http://209.15.123.47:11434/api/generate'
    CHAT_MODEL = os.environ.get('CHAT_MODEL') or 'Qwen3:14b'
    
    # Google Services
    GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID') or '1_YcWW9AWew9afLVk08Tl5lN4iQMhxiQDz4qU3LsB-iE'
    GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    
    # Messaging
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    # App Settings
    DEFAULT_SYSTEM_PROMPT = """คุณคือ AI Assistant ชื่อ "NT AI ONE" ที่ช่วยค้นหาและวิเคราะห์ข้อมูลจาก Google Sheets 
    
ความสามารถของคุณ:
- ค้นหาข้อมูลที่ถูกต้องและครบถ้วน
- วิเคราะห์และสรุปข้อมูล
- ตอบคำถามด้วยภาษาที่เข้าใจง่าย
- ให้ข้อเสนะแนะที่เป็นประโยชน์

กฎการตอบ:
1. ตอบเป็นภาษาไทยที่สุภาพและเป็นมิตร
2. อ้างอิงข้อมูলที่พบจาก sheets
3. หากไม่พบข้อมูล ให้บอกอย่างชัดเจน
4. ใช้รูปแบบที่อ่านง่าย มี bullet points หรือ numbering
"""

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
