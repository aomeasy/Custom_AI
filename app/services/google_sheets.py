import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import os
from app.models.settings import AppSettings

class GoogleSheetsService:
    def __init__(self):
        self.gc = None
        self.sheet_id = None
        self._initialize()
    
    def _initialize(self):
        try:
            # Get credentials from settings or environment
            creds_json = AppSettings.get_setting('google_credentials_json') or os.getenv('GOOGLE_CREDENTIALS_JSON')
            self.sheet_id = AppSettings.get_setting('google_sheets_id') or os.getenv('GOOGLE_SHEETS_ID', '1_YcWW9AWew9afLVk08Tl5lN4iQMhxiQDz4qU3LsB-iE')
            
            if creds_json:
                if isinstance(creds_json, str):
                    creds_dict = json.loads(creds_json)
                else:
                    creds_dict = creds_json
                
                credentials = Credentials.from_service_account_info(creds_dict, scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ])
                self.gc = gspread.authorize(credentials)
                return True
        except Exception as e:
            print(f"Google Sheets initialization error: {e}")
            return False
        return False
    
    def get_user_credentials(self, username, password):
        """ตรวจสอบ user credentials จาก Google Sheets"""
        try:
            if not self.gc or not self.sheet_id:
                return False
            
            # เปิด sheet ชีต1
            sheet = self.gc.open_by_key(self.sheet_id).worksheet('ชีต1')
            
            # อ่านข้อมูล user และ password จาก A2:B
            users_data = sheet.get('A2:B')
            
            for row in users_data:
                if len(row) >= 2 and row[0] == username and row[1] == password:
                    return True
            return False
            
        except Exception as e:
            print(f"Error checking user credentials: {e}")
            return False
    
    def get_all_sheets_data(self):
        """ดึงข้อมูลจากทุกชีตใน Google Sheets"""
        try:
            if not self.gc or not self.sheet_id:
                return {}
            
            spreadsheet = self.gc.open_by_key(self.sheet_id)
            all_data = {}
            
            for worksheet in spreadsheet.worksheets():
                sheet_name = worksheet.title
                try:
                    # ข้าม sheet ที่ใช้สำหรับ authentication
                    if sheet_name in ['ชีต1']:
                        continue
                    
                    data = worksheet.get_all_records()
                    if data:
                        all_data[sheet_name] = data
                except Exception as e:
                    print(f"Error reading sheet {sheet_name}: {e}")
                    continue
            
            return all_data
            
        except Exception as e:
            print(f"Error getting sheets data: {e}")
            return {}
    
    def search_in_sheets(self, query, sheet_names=None):
        """ค้นหาข้อมูลใน sheets"""
        try:
            all_data = self.get_all_sheets_data()
            results = []
            
            query_lower = query.lower()
            
            for sheet_name, data in all_data.items():
                if sheet_names and sheet_name not in sheet_names:
                    continue
                
                for row_idx, row in enumerate(data):
                    for col_name, value in row.items():
                        if str(value).lower().find(query_lower) != -1:
                            results.append({
                                'sheet': sheet_name,
                                'row': row_idx + 1,
                                'column': col_name,
                                'value': value,
                                'full_row': row
                            })
            
            return results
            
        except Exception as e:
            print(f"Error searching in sheets: {e}")
            return []
    
    def get_sheet_summary(self):
        """สรุปข้อมูลใน sheets"""
        try:
            all_data = self.get_all_sheets_data()
            summary = {}
            
            for sheet_name, data in all_data.items():
                summary[sheet_name] = {
                    'rows': len(data),
                    'columns': list(data[0].keys()) if data else [],
                    'total_columns': len(data[0]) if data else 0
                }
            
            return summary
            
        except Exception as e:
            print(f"Error getting sheet summary: {e}")
            return {}
