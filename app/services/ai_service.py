import requests
import json
from app.models.settings import AppSettings
from config import Config

class AIService:
    def __init__(self):
        self.api_url = AppSettings.get_setting('chat_api_url', Config.CHAT_API_URL)
        self.model = AppSettings.get_setting('chat_model', Config.CHAT_MODEL)
        self.system_prompt = AppSettings.get_setting('system_prompt', Config.DEFAULT_SYSTEM_PROMPT)
    
    def generate_response(self, prompt, context=None):
        """Generate AI response with RAG context"""
        try:
            # Prepare the full prompt
            full_prompt = self.system_prompt + "\n\n"
            
            if context:
                full_prompt += f"ข้อมูลที่เกี่ยวข้อง:\n{context}\n\n"
            
            full_prompt += f"คำถาม: {prompt}\n\nคำตอบ:"
            
            # Call the AI API
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'ขออภัย ไม่สามารถสร้างคำตอบได้')
            else:
                return f"Error: API returned status {response.status_code}"
                
        except Exception as e:
            print(f"AI Service Error: {e}")
            return "ขออภัย เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI"
    
    def update_settings(self, api_url=None, model=None, system_prompt=None):
        """Update AI service settings"""
        if api_url:
            AppSettings.set_setting('chat_api_url', api_url)
            self.api_url = api_url
        
        if model:
            AppSettings.set_setting('chat_model', model)
            self.model = model
        
        if system_prompt:
            AppSettings.set_setting('system_prompt', system_prompt)
            self.system_prompt = system_prompt
