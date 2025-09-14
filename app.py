from flask import Flask, render_template, request, jsonify, session
import requests
import json
import os
from datetime import datetime, timedelta
import re
import csv
from io import StringIO
import hashlib
import sqlite3
from collections import defaultdict, Counter
import pickle
import math
from fuzzywuzzy import fuzz
from textblob import TextBlob
import jieba  # For Thai/Chinese text processing
import threading
import time
from functools import lru_cache

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Enhanced Configuration
CHAT_API_URL = "http://209.15.123.47:11434/api/generate"
CHAT_MODEL = "Qwen3:14b"
DEFAULT_SHEET_ID = "1ixUmFKZpub5x6WYtV8pwYU892uQPDlVtjGlxpiEBJNs"

# AI Intelligence Enhancement Classes
class QueryProcessor:
    """Advanced query processing and intent recognition"""
    
    def __init__(self):
        self.intent_patterns = {
            'data_request': {
                'patterns': [
                    r'(ขอ|แสดง|ดู|show|display|view).*(ข้อมูล|data|information)',
                    r'(แถว|row|รายการ|list|record).*(\d+)?(แรก|first|ล่าสุด|latest)?',
                    r'(ทั้งหมด|all|everything|summary|สรุป)',
                ],
                'keywords': ['ข้อมูล', 'แสดง', 'ดู', 'แถว', 'รายการ', 'ทั้งหมด']
            },
            'search_request': {
                'patterns': [
                    r'(หา|ค้นหา|search|find).*(ที่|where|with)',
                    r'(มี|contains|include).*(อะไร|what|ไหน|which)',
                ],
                'keywords': ['หา', 'ค้นหา', 'search', 'find', 'where']
            },
            'analysis_request': {
                'patterns': [
                    r'(วิเคราะห์|analyze|analysis|สถิติ|statistics)',
                    r'(เปรียบเทียบ|compare|comparison)',
                    r'(จำนวน|count|sum|total|รวม)',
                    r'(เฉลี่ย|average|mean|max|min|สูงสุด|ต่ำสุด)',
                ],
                'keywords': ['วิเคราะห์', 'สถิติ', 'เปรียบเทียบ', 'จำนวน', 'เฉลี่ย']
            },
            'help_request': {
                'patterns': [
                    r'(ช่วย|help|สอน|teach|วิธี|how)',
                    r'(คำสั่ง|command|ใช้งาน|usage)',
                ],
                'keywords': ['ช่วย', 'help', 'สอน', 'วิธี', 'คำสั่ง']
            }
        }
    
    def detect_intent(self, query):
        """Detect user intent from query"""
        query_lower = query.lower()
        intents = []
        
        for intent, config in self.intent_patterns.items():
            score = 0
            
            # Pattern matching
            for pattern in config['patterns']:
                if re.search(pattern, query_lower):
                    score += 3
            
            # Keyword matching
            for keyword in config['keywords']:
                if keyword in query_lower:
                    score += 1
            
            if score > 0:
                intents.append({'intent': intent, 'confidence': score})
        
        # Sort by confidence
        intents.sort(key=lambda x: x['confidence'], reverse=True)
        return intents[0] if intents else {'intent': 'general', 'confidence': 0}
    
    def extract_parameters(self, query):
        """Extract parameters from query"""
        params = {
            'numbers': re.findall(r'\d+', query),
            'date_mentions': re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', query),
            'comparison_words': re.findall(r'(มากกว่า|น้อยกว่า|เท่ากับ|>|<|=)', query),
            'aggregation_words': re.findall(r'(รวม|เฉลี่ย|สูงสุด|ต่ำสุด|sum|avg|max|min)', query)
        }
        return params

class DataAnalyzer:
    """Advanced data analysis capabilities"""
    
    @staticmethod
    def analyze_data(data, query_params):
        """Perform data analysis based on query parameters"""
        if not data or len(data) < 2:
            return None
        
        try:
            headers = data[0] if data else []
            rows = data[1:] if len(data) > 1 else []
            
            analysis = {
                'basic_stats': DataAnalyzer.get_basic_stats(rows, headers),
                'summary': DataAnalyzer.get_summary(rows, headers),
                'patterns': DataAnalyzer.find_patterns(rows, headers)
            }
            
            # Advanced analysis based on query
            if query_params.get('aggregation_words'):
                analysis['aggregations'] = DataAnalyzer.calculate_aggregations(rows, headers)
            
            return analysis
        except Exception as e:
            print(f"[DEBUG] Analysis error: {e}")
            return None
    
    @staticmethod
    def get_basic_stats(rows, headers):
        """Calculate basic statistics"""
        stats = {
            'total_rows': len(rows),
            'total_columns': len(headers),
            'numeric_columns': [],
            'text_columns': []
        }
        
        if not rows:
            return stats
        
        # Analyze column types
        for col_idx, header in enumerate(headers):
            numeric_count = 0
            total_count = 0
            
            for row in rows[:10]:  # Sample first 10 rows
                if col_idx < len(row) and row[col_idx]:
                    try:
                        float(row[col_idx])
                        numeric_count += 1
                    except:
                        pass
                    total_count += 1
            
            if total_count > 0 and numeric_count / total_count > 0.7:
                stats['numeric_columns'].append(header)
            else:
                stats['text_columns'].append(header)
        
        return stats
    
    @staticmethod
    def get_summary(rows, headers):
        """Generate data summary"""
        if not rows:
            return "ไม่มีข้อมูลในตาราง"
        
        summary_parts = []
        summary_parts.append(f"ข้อมูลทั้งหมด {len(rows)} แถว")
        summary_parts.append(f"มี {len(headers)} คอลัมน์: {', '.join(headers[:5])}")
        
        if len(headers) > 5:
            summary_parts.append("และอื่นๆ...")
        
        return " ".join(summary_parts)
    
    @staticmethod
    def calculate_aggregations(rows, headers):
        """Calculate aggregations for numeric columns"""
        aggregations = {}
        
        for col_idx, header in enumerate(headers):
            values = []
            for row in rows:
                if col_idx < len(row) and row[col_idx]:
                    try:
                        values.append(float(row[col_idx]))
                    except:
                        continue
            
            if values:
                aggregations[header] = {
                    'count': len(values),
                    'sum': sum(values),
                    'avg': sum(values) / len(values),
                    'max': max(values),
                    'min': min(values)
                }
        
        return aggregations
    
    @staticmethod
    def find_patterns(rows, headers):
        """Find patterns in data"""
        patterns = []
        
        if not rows:
            return patterns
        
        # Find most common values
        for col_idx, header in enumerate(headers[:3]):  # Check first 3 columns
            values = []
            for row in rows:
                if col_idx < len(row) and row[col_idx]:
                    values.append(row[col_idx])
            
            if values:
                counter = Counter(values)
                most_common = counter.most_common(3)
                if most_common:
                    patterns.append(f"{header}: ข้อมูลที่พบบ่อย - {', '.join([f'{v} ({c} ครั้ง)' for v, c in most_common])}")
        
        return patterns

class SmartSearch:
    """Enhanced search with fuzzy matching and context awareness"""
    
    def __init__(self):
        self.cache = {}
        self.search_history = []
    
    @lru_cache(maxsize=100)
    def fuzzy_search(self, query, data_str):
        """Perform fuzzy search with caching"""
        return fuzz.partial_ratio(query.lower(), data_str.lower())
    
    def smart_search(self, query, data, intent):
        """Intelligent search based on intent and context"""
        if not data:
            return "ไม่สามารถเข้าถึงข้อมูลได้ในขณะนี้"
        
        print(f"[DEBUG] Smart search - Intent: {intent['intent']}, Query: '{query}'")
        
        # Process based on intent
        if intent['intent'] == 'data_request':
            return self.handle_data_request(query, data, intent)
        elif intent['intent'] == 'search_request':
            return self.handle_search_request(query, data, intent)
        elif intent['intent'] == 'analysis_request':
            return self.handle_analysis_request(query, data, intent)
        else:
            return self.handle_general_search(query, data, intent)
    
    def handle_data_request(self, query, data, intent):
        """Handle data viewing requests"""
        # Extract number of rows requested
        numbers = re.findall(r'\d+', query)
        requested_rows = int(numbers[0]) if numbers else 5
        requested_rows = min(requested_rows, 20)  # Limit to 20 rows
        
        result_rows = []
        headers = data[0] if data else []
        
        # Add headers
        if headers:
            result_rows.append(f"หัวข้อคอลัมน์: {' | '.join(headers)}")
            result_rows.append("-" * 50)
        
        # Add data rows
        for i in range(1, min(requested_rows + 1, len(data))):
            if i < len(data) and data[i]:
                row_display = ' | '.join([str(cell) if cell else '' for cell in data[i]])
                result_rows.append(f"แถวที่ {i}: {row_display}")
        
        if result_rows:
            # Add analysis
            analyzer = DataAnalyzer()
            analysis = analyzer.analyze_data(data, {})
            if analysis:
                result_rows.append("\n📊 สรุปข้อมูล:")
                result_rows.append(analysis['summary'])
        
        return "\n".join(result_rows) if result_rows else "ไม่พบข้อมูลใน Google Sheets"
    
    def handle_search_request(self, query, data, intent):
        """Handle specific search requests"""
        query_lower = query.lower()
        results = []
        
        # Enhanced search with fuzzy matching
        for row_idx, row in enumerate(data):
            row_score = 0
            matched_cells = []
            
            for col_idx, cell in enumerate(row):
                if cell:
                    cell_str = str(cell)
                    
                    # Exact match (highest priority)
                    if query_lower in cell_str.lower():
                        row_score += 10
                        matched_cells.append(f"คอลัมน์ {col_idx + 1}: {cell_str}")
                    
                    # Fuzzy match
                    fuzzy_score = self.fuzzy_search(query, cell_str)
                    if fuzzy_score > 70:  # 70% similarity threshold
                        row_score += fuzzy_score / 10
                        matched_cells.append(f"คอลัมน์ {col_idx + 1}: {cell_str} (คล้าย {fuzzy_score}%)")
            
            if row_score > 0:
                results.append({
                    'row_idx': row_idx,
                    'score': row_score,
                    'row_data': row,
                    'matches': matched_cells
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if results:
            formatted_results = []
            for result in results[:5]:  # Top 5 results
                row_display = ' | '.join([str(cell) if cell else '' for cell in result['row_data']])
                formatted_results.append(f"แถวที่ {result['row_idx'] + 1}: {row_display}")
                formatted_results.append(f"  └─ พบใน: {', '.join(result['matches'][:2])}")
            
            return "\n".join(formatted_results)
        else:
            return self.suggest_alternatives(query, data)
    
    def handle_analysis_request(self, query, data, intent):
        """Handle data analysis requests"""
        analyzer = DataAnalyzer()
        query_processor = QueryProcessor()
        
        params = query_processor.extract_parameters(query)
        analysis = analyzer.analyze_data(data, params)
        
        if not analysis:
            return "ไม่สามารถวิเคราะห์ข้อมูลได้"
        
        result_parts = []
        
        # Basic statistics
        if analysis.get('basic_stats'):
            stats = analysis['basic_stats']
            result_parts.append("📊 สถิติพื้นฐาน:")
            result_parts.append(f"  • จำนวนแถว: {stats['total_rows']}")
            result_parts.append(f"  • จำนวนคอลัมน์: {stats['total_columns']}")
            
            if stats['numeric_columns']:
                result_parts.append(f"  • คอลัมน์ตัวเลข: {', '.join(stats['numeric_columns'])}")
            
            if stats['text_columns']:
                result_parts.append(f"  • คอลัมน์ข้อความ: {', '.join(stats['text_columns'][:3])}")
        
        # Aggregations
        if analysis.get('aggregations'):
            result_parts.append("\n🔢 การคำนวณ:")
            for col, agg in list(analysis['aggregations'].items())[:3]:
                result_parts.append(f"  • {col}:")
                result_parts.append(f"    - จำนวน: {agg['count']}")
                result_parts.append(f"    - รวม: {agg['sum']:.2f}")
                result_parts.append(f"    - เฉลี่ย: {agg['avg']:.2f}")
                result_parts.append(f"    - สูงสุด: {agg['max']:.2f}")
                result_parts.append(f"    - ต่ำสุด: {agg['min']:.2f}")
        
        # Patterns
        if analysis.get('patterns'):
            result_parts.append("\n🔍 รูปแบบที่พบ:")
            for pattern in analysis['patterns'][:3]:
                result_parts.append(f"  • {pattern}")
        
        return "\n".join(result_parts)
    
    def handle_general_search(self, query, data, intent):
        """Handle general queries"""
        return self.handle_search_request(query, data, intent)
    
    def suggest_alternatives(self, query, data):
        """Suggest alternative searches when no results found"""
        suggestions = []
        
        # Get available column names
        headers = data[0] if data else []
        if headers:
            suggestions.append(f"คอลัมน์ที่มี: {', '.join(headers[:5])}")
        
        # Get sample data
        if len(data) > 1:
            sample_values = []
            for row in data[1:3]:  # First 2 data rows
                for cell in row[:3]:  # First 3 cells
                    if cell and len(str(cell)) > 2:
                        sample_values.append(str(cell))
            
            if sample_values:
                suggestions.append(f"ข้อมูลตัวอย่าง: {', '.join(sample_values[:5])}")
        
        result = "ไม่พบข้อมูลที่ตรงกับคำค้นหา\n\n💡 คำแนะนำ:"
        for suggestion in suggestions:
            result += f"\n  • {suggestion}"
        
        return result

class ConversationMemory:
    """Remember conversation context and learning from interactions"""
    
    def __init__(self):
        self.conversation_history = []
        self.user_preferences = {}
        self.frequent_queries = Counter()
    
    def add_interaction(self, query, response, context_found):
        """Add interaction to memory"""
        interaction = {
            'timestamp': datetime.now(),
            'query': query,
            'response': response,
            'context_found': context_found,
            'query_hash': hashlib.md5(query.lower().encode()).hexdigest()
        }
        
        self.conversation_history.append(interaction)
        self.frequent_queries[query.lower()] += 1
        
        # Keep only last 100 interactions
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]
    
    def get_context(self, current_query):
        """Get relevant context from conversation history"""
        if not self.conversation_history:
            return None
        
        # Find similar previous queries
        similar_interactions = []
        current_query_lower = current_query.lower()
        
        for interaction in self.conversation_history[-10:]:  # Last 10 interactions
            similarity = fuzz.partial_ratio(current_query_lower, interaction['query'].lower())
            if similarity > 60:
                similar_interactions.append(interaction)
        
        return similar_interactions[-1] if similar_interactions else None
    
    def get_popular_queries(self):
        """Get most popular queries"""
        return self.frequent_queries.most_common(5)

# Enhanced main functions
query_processor = QueryProcessor()
smart_search = SmartSearch()
conversation_memory = ConversationMemory()

def enhanced_search_sheet_data(query):
    """Enhanced search with AI intelligence"""
    try:
        print(f"[DEBUG] Enhanced search for query: '{query}'")
        data = get_google_sheet_data(app_settings['google_sheet_id'])
        
        if not data:
            print("[DEBUG] No data returned from Google Sheets")
            return "ไม่สามารถเข้าถึงข้อมูลได้ในขณะนี้"
        
        # Detect intent
        intent = query_processor.detect_intent(query)
        print(f"[DEBUG] Detected intent: {intent}")
        
        # Get conversation context
        context = conversation_memory.get_context(query)
        if context:
            print(f"[DEBUG] Found similar previous query: {context['query']}")
        
        # Perform smart search
        result = smart_search.smart_search(query, data, intent)
        
        # Remember this interaction
        context_found = bool(result and 'ไม่พบข้อมูล' not in result and 'ไม่สามารถเข้าถึงข้อมูล' not in result)
        conversation_memory.add_interaction(query, result, context_found)
        
        return result
        
    except Exception as e:
        print(f"[DEBUG] Enhanced search error: {e}")
        import traceback
        traceback.print_exc()
        return f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"

def enhanced_call_ai_model(prompt, context=""):
    """Enhanced AI model call with better prompting"""
    try:
        # Get conversation context
        conversation_context = conversation_memory.get_context(prompt)
        context_info = ""
        if conversation_context:
            context_info = f"\nบริบทจากการสนทนาก่อนหน้า: {conversation_context['query']} -> {conversation_context['response'][:100]}..."
        
        # Enhanced system prompt with advanced instructions
        enhanced_system_prompt = f"""{app_settings['system_prompt']}

🧠 คำแนะนำขั้นสูงสำหรับการตอบ:
1. วิเคราะห์เจตนาของผู้ใช้ก่อนตอบ
2. หากมีข้อมูลใน Context ให้นำมาใช้อย่างชาญฉลาด
3. จัดรูปแบบคำตอบให้อ่านง่าย ใส่อีโมจิที่เหมาะสม
4. ให้คำแนะนำเพิ่มเติมหากเป็นประโยชน์
5. หากไม่มีข้อมูลที่ตรงกัน ให้แนะนำทางเลือกอื่น

📊 เมื่อแสดงข้อมูล:
- ใส่หัวข้อชัดเจน
- จัดรูปแบบเป็นตาราง หรือจุดย่อย
- เพิ่มสรุปหรือข้อสังเกตที่น่าสนใจ

🔍 เมื่อค้นหาข้อมูล:
- บอกจำนวนผลลัพธ์ที่พบ
- เรียงลำดับตามความเกี่ยวข้อง
- แนะนำคำค้นหาที่ดีกว่าหากไม่พบ

{context_info}"""
        
        full_prompt = f"{enhanced_system_prompt}\n\nข้อมูลจาก Google Sheets:\n{context}\n\nคำถามของผู้ใช้: {prompt}"
        
        payload = {
            "model": CHAT_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }
        }
        
        print(f"[DEBUG] Calling enhanced AI model: {CHAT_MODEL}")
        print(f"[DEBUG] Prompt length: {len(full_prompt)} characters")
        print(f"[DEBUG] Context preview: {context[:200]}...")
        
        response = requests.post(CHAT_API_URL, json=payload, timeout=45)
        
        print(f"[DEBUG] AI response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', 'ไม่สามารถสร้างคำตอบได้')
            
            # Post-process response
            ai_response = post_process_response(ai_response, context)
            
            print(f"[DEBUG] AI response length: {len(ai_response)} characters")
            return ai_response
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            print(f"[DEBUG] AI error: {error_msg}")
            return "ขออภัย เกิดข้อผิดพลาดในการเชื่อมต่อ AI โปรดลองใหม่อีกครั้ง"
            
    except Exception as e:
        print(f"[DEBUG] Enhanced AI Model error: {e}")
        import traceback
        traceback.print_exc()
        return "เกิดข้อผิดพลาดในการประมวลผล โปรดลองใหม่อีกครั้ง"

def post_process_response(response, context):
    """Post-process AI response for better quality"""
    try:
        # Add helpful suggestions if response is too short
        if len(response) < 50 and context:
            response += "\n\n💡 คุณสามารถถามเพิ่มเติม เช่น:\n"
            response += "  • ขอดูข้อมูลเพิ่มเติม\n"
            response += "  • วิเคราะห์ข้อมูลนี้\n"
            response += "  • เปรียบเทียบข้อมูล"
        
        # Add popular queries suggestion
        popular = conversation_memory.get_popular_queries()
        if popular and len(response) < 100:
            response += "\n\n🔥 คำถามยอดนิยม:\n"
            for query, count in popular[:3]:
                if len(query) < 50:
                    response += f"  • {query}\n"
        
        return response
        
    except Exception as e:
        print(f"[DEBUG] Post-process error: {e}")
        return response

# Enhanced API endpoints
@app.route('/')
def index():
    """หน้าแรกของแอปพลิเคชัน"""
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """จัดการการเข้าสู่ระบบ"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Default credentials
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            session['username'] = username
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """ออกจากระบบ"""
    session.clear()
    return redirect('/')
    
@app.route('/api/enhanced-chat', methods=['POST'])
def enhanced_chat():
    """Enhanced chat endpoint with AI intelligence"""
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        message = data.get('message', '')
        
        print(f"[DEBUG] Enhanced chat message: '{message}'")
        
        if not message:
            return jsonify({'error': 'กรุณาใส่ข้อความ'})
        
        # Enhanced search with AI intelligence
        print("[DEBUG] Starting enhanced Google Sheets search...")
        context = enhanced_search_sheet_data(message)
        
        # Enhanced AI response
        print("[DEBUG] Starting enhanced AI model call...")
        ai_response = enhanced_call_ai_model(message, context)
        
        context_found = bool(context and 'ไม่พบข้อมูล' not in context and 'ไม่สามารถเข้าถึงข้อมูล' not in context)
        
        # Detect intent for response metadata
        intent = query_processor.detect_intent(message)
        
        print(f"[DEBUG] Enhanced chat completed - Intent: {intent['intent']}, Context found: {context_found}")
        
        return jsonify({
            'response': ai_response,
            'context_found': context_found,
            'intent': intent,
            'timestamp': datetime.now().isoformat(),
            'debug_info': {
                'context_preview': context[:150] + '...' if len(context) > 150 else context,
                'sheet_id': app_settings['google_sheet_id'],
                'conversation_count': len(conversation_memory.conversation_history)
            }
        })
        
    except Exception as e:
        print(f"[DEBUG] Enhanced chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'เกิดข้อผิดพลาดในการประมวลผล'}), 500

@app.route('/api/conversation-stats', methods=['GET'])
def conversation_stats():
    """Get conversation statistics"""
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        popular_queries = conversation_memory.get_popular_queries()
        recent_interactions = conversation_memory.conversation_history[-5:] if conversation_memory.conversation_history else []
        
        stats = {
            'total_interactions': len(conversation_memory.conversation_history),
            'popular_queries': [{'query': q, 'count': c} for q, c in popular_queries],
            'recent_interactions': [
                {
                    'query': interaction['query'][:50] + '...' if len(interaction['query']) > 50 else interaction['query'],
                    'timestamp': interaction['timestamp'].isoformat(),
                    'context_found': interaction['context_found']
                }
                for interaction in recent_interactions
            ]
        }
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"[DEBUG] Stats error: {e}")
        return jsonify({'error': 'เกิดข้อผิดพลาดในการดึงสถิติ'}), 500

# Update settings to include enhanced options
app_settings = {
    'system_prompt': '''คุณเป็น AI Assistant ที่ช่วยค้นหาและวิเคราะห์ข้อมูลจาก Google Sheets อย่างชาญฉลาด 
    ตอบคำถามด้วยความเป็นมิตรและให้ข้อมูลที่ถูกต้อง ใช้อีโมจิให้เหมาะสม จัดรูปแบบให้อ่านง่าย 
    และให้คำแนะนำที่เป็นประโยชน์เสมอ''',
    'google_sheet_id': DEFAULT_SHEET_ID,
    'line_token': '',
    'telegram_api': '',
    'ai_temperature': 0.7,
    'max_response_length': 2048,
    'enable_fuzzy_search': True,
    'enable_analytics': True,
    'conversation_memory': True,
    # เพิ่มส่วนนี้
    'default_credentials': {
        'username': 'admin',
        'password': 'password'
    }
}

# Additional utility functions for enhanced functionality
class DataValidator:
    """Validate and clean data for better processing"""
    
    @staticmethod
    def validate_sheet_data(data):
        """Validate and clean sheet data"""
        if not data:
            return None
        
        cleaned_data = []
        for row_idx, row in enumerate(data):
            cleaned_row = []
            for cell in row:
                if cell is not None:
                    # Clean whitespace and special characters
                    cleaned_cell = str(cell).strip()
                    # Handle Thai encoding issues
                    try:
                        cleaned_cell = cleaned_cell.encode('utf-8').decode('utf-8')
                    except:
                        pass
                    cleaned_row.append(cleaned_cell)
                else:
                    cleaned_row.append('')
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
    
    @staticmethod
    def detect_data_types(data):
        """Detect data types in columns"""
        if not data or len(data) < 2:
            return {}
        
        headers = data[0]
        rows = data[1:]
        column_types = {}
        
        for col_idx, header in enumerate(headers):
            types = {'number': 0, 'date': 0, 'text': 0, 'empty': 0}
            total_samples = 0
            
            for row in rows[:20]:  # Sample first 20 rows
                if col_idx < len(row):
                    cell = row[col_idx]
                    if not cell:
                        types['empty'] += 1
                    else:
                        total_samples += 1
                        # Check if number
                        try:
                            float(cell)
                            types['number'] += 1
                        except:
                            # Check if date
                            if re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', str(cell)):
                                types['date'] += 1
                            else:
                                types['text'] += 1
            
            if total_samples > 0:
                dominant_type = max(types, key=types.get)
                confidence = types[dominant_type] / total_samples
                column_types[header] = {'type': dominant_type, 'confidence': confidence}
        
        return column_types

class ResponseFormatter:
    """Format responses for better readability"""
    
    @staticmethod
    def format_table_data(data, max_rows=10):
        """Format data as a readable table"""
        if not data:
            return "ไม่มีข้อมูล"
        
        headers = data[0] if data else []
        rows = data[1:max_rows+1] if len(data) > 1 else []
        
        if not headers:
            return "ไม่พบหัวข้อคอลัมน์"
        
        # Calculate column widths
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in rows:
                if i < len(row) and row[i]:
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(min(max_width, 20))  # Limit to 20 chars
        
        # Format table
        formatted = []
        
        # Headers
        header_row = "| " + " | ".join([str(h)[:w].ljust(w) for h, w in zip(headers, col_widths)]) + " |"
        separator = "|" + "|".join(["-" * (w + 2) for w in col_widths]) + "|"
        
        formatted.append("📊 **ตารางข้อมูล**")
        formatted.append("```")
        formatted.append(header_row)
        formatted.append(separator)
        
        # Data rows
        for row_idx, row in enumerate(rows):
            cells = []
            for col_idx, width in enumerate(col_widths):
                cell = row[col_idx] if col_idx < len(row) else ""
                cell_str = str(cell)[:width].ljust(width) if cell else " " * width
                cells.append(cell_str)
            formatted.append("| " + " | ".join(cells) + " |")
        
        formatted.append("```")
        
        if len(data) > max_rows + 1:
            formatted.append(f"... และอีก {len(data) - max_rows - 1} แถว")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_search_results(results, query):
        """Format search results nicely"""
        if not results:
            return f"🔍 ไม่พบข้อมูลที่ตรงกับ \"{query}\""
        
        formatted = [f"🔍 **ผลการค้นหา: \"{query}\"**\n"]
        
        for idx, result in enumerate(results[:5], 1):
            formatted.append(f"**{idx}.** {result}")
            if idx < len(results):
                formatted.append("")
        
        if len(results) > 5:
            formatted.append(f"\n... และอีก {len(results) - 5} ผลลัพธ์")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_analysis_result(analysis):
        """Format analysis results"""
        if not analysis:
            return "ไม่สามารถวิเคราะห์ข้อมูลได้"
        
        formatted = ["📈 **การวิเคราะห์ข้อมูล**\n"]
        
        # Basic stats
        if 'basic_stats' in analysis:
            stats = analysis['basic_stats']
            formatted.append("**📊 สถิติพื้นฐาน:**")
            formatted.append(f"• จำนวนแถว: {stats.get('total_rows', 0):,}")
            formatted.append(f"• จำนวนคอลัมน์: {stats.get('total_columns', 0)}")
            
            if stats.get('numeric_columns'):
                formatted.append(f"• คอลัมน์ตัวเลข: {', '.join(stats['numeric_columns'][:5])}")
            
            formatted.append("")
        
        # Aggregations
        if 'aggregations' in analysis:
            formatted.append("**🔢 การคำนวณ:**")
            for col, agg in list(analysis['aggregations'].items())[:3]:
                formatted.append(f"• **{col}:**")
                formatted.append(f"  - จำนวน: {agg['count']:,}")
                formatted.append(f"  - รวม: {agg['sum']:,.2f}")
                formatted.append(f"  - เฉลี่ย: {agg['avg']:,.2f}")
                formatted.append(f"  - สูงสุด: {agg['max']:,.2f}")
                formatted.append(f"  - ต่ำสุด: {agg['min']:,.2f}")
                formatted.append("")
        
        # Patterns
        if 'patterns' in analysis:
            formatted.append("**🔍 รูปแบบที่พบ:**")
            for pattern in analysis['patterns']:
                formatted.append(f"• {pattern}")
        
        return "\n".join(formatted)

class QuickCommands:
    """Handle quick commands and shortcuts"""
    
    COMMANDS = {
        'help': 'แสดงคำสั่งที่ใช้ได้',
        'data': 'แสดงข้อมูล 5 แถวแรก',
        'all': 'แสดงข้อมูลทั้งหมด (จำกัด 20 แถว)',
        'stats': 'แสดงสถิติข้อมูล',
        'headers': 'แสดงหัวข้อคอลัมน์',
        'clear': 'ล้างประวัติการสนทนา',
        'popular': 'แสดงคำถามยอดนิยม'
    }
    
    @staticmethod
    def is_command(query):
        """Check if query is a command"""
        query_clean = query.strip().lower()
        return query_clean in QuickCommands.COMMANDS or query_clean.startswith('/')
    
    @staticmethod
    def execute_command(query, data, memory):
        """Execute quick command"""
        query_clean = query.strip().lower().replace('/', '')
        
        if query_clean == 'help':
            help_text = ["🤖 **คำสั่งที่ใช้ได้:**\n"]
            for cmd, desc in QuickCommands.COMMANDS.items():
                help_text.append(f"• `{cmd}` - {desc}")
            help_text.append("\n💡 **ตัวอย่างคำถาม:**")
            help_text.append("• ขอดูข้อมูล 10 แถว")
            help_text.append("• หาข้อมูลที่มีคำว่า 'xyz'")
            help_text.append("• วิเคราะห์ข้อมูลในคอลัมน์ ABC")
            help_text.append("• เปรียบเทียบข้อมูลเดือนนี้กับเดือนที่แล้ว")
            return "\n".join(help_text)
        
        elif query_clean == 'data':
            if data and len(data) > 1:
                formatter = ResponseFormatter()
                return formatter.format_table_data(data, 5)
            return "ไม่มีข้อมูลในระบบ"
        
        elif query_clean == 'all':
            if data and len(data) > 1:
                formatter = ResponseFormatter()
                return formatter.format_table_data(data, 20)
            return "ไม่มีข้อมูลในระบบ"
        
        elif query_clean == 'stats':
            if data:
                analyzer = DataAnalyzer()
                analysis = analyzer.analyze_data(data, {})
                formatter = ResponseFormatter()
                return formatter.format_analysis_result(analysis)
            return "ไม่มีข้อมูลในระบบ"
        
        elif query_clean == 'headers':
            if data and data[0]:
                headers = data[0]
                result = ["📝 **หัวข้อคอลัมน์:**\n"]
                for i, header in enumerate(headers, 1):
                    result.append(f"{i}. {header}")
                return "\n".join(result)
            return "ไม่พบหัวข้อคอลัมน์"
        
        elif query_clean == 'clear':
            memory.conversation_history.clear()
            memory.frequent_queries.clear()
            return "✅ ล้างประวัติการสนทนาเรียบร้อยแล้ว"
        
        elif query_clean == 'popular':
            popular = memory.get_popular_queries()
            if popular:
                result = ["🔥 **คำถามยอดนิยม:**\n"]
                for i, (query, count) in enumerate(popular, 1):
                    result.append(f"{i}. {query} ({count} ครั้ง)")
                return "\n".join(result)
            return "ยังไม่มีคำถามในระบบ"
        
        return "ไม่พบคำสั่งนี้ พิมพ์ 'help' เพื่อดูคำสั่งที่ใช้ได้"

# Update the enhanced search function to use new features
def ultra_enhanced_search_sheet_data(query):
    """Ultra enhanced search with all features"""
    try:
        print(f"[DEBUG] Ultra enhanced search for query: '{query}'")
        
        # Get and validate data
        raw_data = get_google_sheet_data(app_settings['google_sheet_id'])
        if not raw_data:
            return "ไม่สามารถเข้าถึงข้อมูลได้ในขณะนี้"
        
        # Clean and validate data
        validator = DataValidator()
        data = validator.validate_sheet_data(raw_data)
        
        # Check for quick commands
        if QuickCommands.is_command(query):
            return QuickCommands.execute_command(query, data, conversation_memory)
        
        # Detect intent and parameters
        intent = query_processor.detect_intent(query)
        params = query_processor.extract_parameters(query)
        
        print(f"[DEBUG] Intent: {intent}, Parameters: {params}")
        
        # Get conversation context
        context = conversation_memory.get_context(query)
        
        # Perform intelligent search based on intent
        if intent['intent'] == 'data_request':
            formatter = ResponseFormatter()
            numbers = params.get('numbers', [])
            requested_rows = int(numbers[0]) if numbers else 10
            
            if any(word in query.lower() for word in ['ทั้งหมด', 'all', 'everything']):
                requested_rows = 20
            
            result = formatter.format_table_data(data, requested_rows)
            
            # Add quick analysis
            if len(data) > 1:
                analyzer = DataAnalyzer()
                analysis = analyzer.analyze_data(data, params)
                if analysis and analysis.get('summary'):
                    result += f"\n\n💡 **สรุป:** {analysis['summary']}"
            
        elif intent['intent'] == 'analysis_request':
            analyzer = DataAnalyzer()
            analysis = analyzer.analyze_data(data, params)
            formatter = ResponseFormatter()
            result = formatter.format_analysis_result(analysis)
            
        elif intent['intent'] == 'search_request':
            # Enhanced fuzzy search
            search_results = []
            query_lower = query.lower()
            
            # Remove common words
            stop_words = ['หา', 'ค้นหา', 'ที่', 'มี', 'ใน', 'the', 'in', 'with', 'find', 'search']
            search_terms = [word for word in query_lower.split() if word not in stop_words and len(word) > 1]
            
            if not search_terms:
                search_terms = [query_lower]
            
            for row_idx, row in enumerate(data):
                row_score = 0
                matched_terms = []
                
                for col_idx, cell in enumerate(row):
                    if cell:
                        cell_lower = str(cell).lower()
                        for term in search_terms:
                            if term in cell_lower:
                                row_score += 10
                                matched_terms.append(term)
                            elif app_settings.get('enable_fuzzy_search', True):
                                fuzzy_score = fuzz.partial_ratio(term, cell_lower)
                                if fuzzy_score > 75:
                                    row_score += fuzzy_score / 10
                                    matched_terms.append(f"{term}~{fuzzy_score}%")
                
                if row_score > 0:
                    row_display = ' | '.join([str(cell)[:30] + ('...' if len(str(cell)) > 30 else '') 
                                            for cell in row if cell])
                    search_results.append({
                        'row_idx': row_idx,
                        'score': row_score,
                        'display': f"แถวที่ {row_idx + 1}: {row_display}",
                        'matches': matched_terms
                    })
            
            # Sort and format results
            search_results.sort(key=lambda x: x['score'], reverse=True)
            
            formatter = ResponseFormatter()
            if search_results:
                formatted_results = []
                for result in search_results[:8]:  # Top 8 results
                    formatted_results.append(result['display'])
                    if result['matches']:
                        formatted_results.append(f"  🎯 ตรงกับ: {', '.join(result['matches'][:3])}")
                
                result = formatter.format_search_results(formatted_results, ' '.join(search_terms))
            else:
                result = f"🔍 ไม่พบข้อมูลที่ตรงกับ \"{query}\"\n\n"
                result += "💡 **คำแนะนำ:**\n"
                result += "• ลองใช้คำค้นหาที่สั้นกว่า\n"
                result += "• ตรวจสอบการสะกดคำ\n"
                result += "• ใช้คำสั่ง 'headers' เพื่อดูคอลัมน์ที่มี\n"
                result += "• ใช้คำสั่ง 'data' เพื่อดูข้อมูลตัวอย่าง"
        
        else:
            # General query handling
            smart_search_instance = SmartSearch()
            result = smart_search_instance.smart_search(query, data, intent)
        
        # Remember interaction
        context_found = bool(result and 'ไม่พบข้อมูล' not in result and 'ไม่สามารถเข้าถึงข้อมูล' not in result)
        conversation_memory.add_interaction(query, result[:200], context_found)
        
        return result
        
    except Exception as e:
        print(f"[DEBUG] Ultra enhanced search error: {e}")
        import traceback
        traceback.print_exc()
        return f"เกิดข้อผิดพลาดในการค้นหา: {str(e)}"

# Replace the original functions in your Flask app
def get_google_sheet_data(sheet_id, range_name="A:Z"):
    """Enhanced Google Sheets data fetching with caching"""
    try:
        # Check cache first (simple in-memory cache)
        cache_key = f"{sheet_id}_{range_name}"
        current_time = datetime.now()
        
        # Cache for 5 minutes
        if hasattr(get_google_sheet_data, 'cache'):
            cached_data, cached_time = get_google_sheet_data.cache.get(cache_key, (None, None))
            if cached_data and cached_time and (current_time - cached_time).seconds < 300:
                print(f"[DEBUG] Using cached Google Sheets data")
                return cached_data
        
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        print(f"[DEBUG] Fetching Google Sheet: {csv_url}")
        
        response = requests.get(csv_url, timeout=15)
        print(f"[DEBUG] Google Sheets response status: {response.status_code}")
        
        if response.status_code == 200:
            # Better CSV parsing
            csv_data = StringIO(response.text)
            reader = csv.reader(csv_data)
            data = []
            
            for row_num, row in enumerate(reader):
                # Clean empty rows
                if any(cell.strip() for cell in row):
                    data.append(row)
                if row_num == 0:
                    print(f"[DEBUG] Headers: {row}")
            
            print(f"[DEBUG] Successfully parsed {len(data)} rows from Google Sheets")
            
            # Cache the data
            if not hasattr(get_google_sheet_data, 'cache'):
                get_google_sheet_data.cache = {}
            get_google_sheet_data.cache[cache_key] = (data, current_time)
            
            return data
        else:
            print(f"[DEBUG] Google Sheets error: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[DEBUG] Error fetching Google Sheets data: {e}")
        return None

# Updated chat endpoint to use ultra enhanced features
@app.route('/api/ultra-chat', methods=['POST'])
def ultra_chat():
    """Ultra enhanced chat with all AI features"""
    if not session.get('logged_in'):
        return jsonify({'error': 'กรุณาเข้าสู่ระบบก่อน'}), 401
    
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'กรุณาใส่ข้อความ'})
        
        print(f"[DEBUG] Ultra chat message: '{message}'")
        
        # Ultra enhanced search
        context = ultra_enhanced_search_sheet_data(message)
        
        # Enhanced AI response (only if not a direct command response)
        if not QuickCommands.is_command(message):
            ai_response = enhanced_call_ai_model(message, context)
            
            # Combine context and AI response intelligently
            if context and len(context) > 100:
                final_response = context  # Use processed data directly
                if len(ai_response) > 50 and 'ข้อผิดพลาด' not in ai_response:
                    final_response += f"\n\n🤖 **AI ช่วยเหลือ:**\n{ai_response}"
            else:
                final_response = ai_response
        else:
            final_response = context
        
        # Detect response type
        intent = query_processor.detect_intent(message)
        context_found = bool(context and 'ไม่พบข้อมูล' not in context)
        
        # Add helpful suggestions
        suggestions = []
        if context_found:
            suggestions = [
                "วิเคราะห์ข้อมูลนี้เพิ่มเติม",
                "แสดงข้อมูลในรูปแบบอื่น",
                "เปรียบเทียบกับข้อมูลอื่น"
            ]
        else:
            suggestions = [
                "พิมพ์ 'help' เพื่อดูคำสั่งที่ใช้ได้",
                "พิมพ์ 'data' เพื่อดูข้อมูลตัวอย่าง",
                "พิมพ์ 'headers' เพื่อดูคอลัมน์ที่มี"
            ]
        
        response_data = {
            'response': final_response,
            'context_found': context_found,
            'intent': intent,
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'conversation_count': len(conversation_memory.conversation_history),
                'popular_queries_count': len(conversation_memory.frequent_queries)
            }
        }
        
        print(f"[DEBUG] Ultra chat completed - Intent: {intent['intent']}, Context: {context_found}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[DEBUG] Ultra chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'เกิดข้อผิดพลาดในการประมวลผล'}), 500

if __name__ == '__main__':
    print("[DEBUG] Starting Ultra Enhanced AI Flask application...")
    print(f"[DEBUG] Features enabled: Fuzzy Search, Analytics, Conversation Memory")
    print(f"[DEBUG] Quick commands available: {list(QuickCommands.COMMANDS.keys())}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
