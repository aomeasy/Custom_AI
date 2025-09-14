from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
from app.services.google_sheets import GoogleSheetsService

class RAGEngine:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.index = None
        self.documents = []
        self.sheets_service = GoogleSheetsService()
        self.load_documents()
    
    def load_documents(self):
        """Load and index documents from Google Sheets"""
        try:
            # Get data from Google Sheets
            sheets_data = self.sheets_service.get_all_sheets_data()
            
            documents = []
            for sheet_name, data in sheets_data.items():
                for row_idx, row in enumerate(data):
                    # Convert row to searchable text
                    row_text = f"Sheet: {sheet_name}\n"
                    for col, value in row.items():
                        if value:
                            row_text += f"{col}: {value}\n"
                    
                    documents.append({
                        'text': row_text,
                        'sheet': sheet_name,
                        'row_data': row,
                        'row_index': row_idx
                    })
            
            if documents:
                # Create embeddings
                texts = [doc['text'] for doc in documents]
                embeddings = self.model.encode(texts)
                
                # Create FAISS index
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                self.index.add(embeddings.astype('float32'))
                
                self.documents = documents
                print(f"Loaded {len(documents)} documents from Google Sheets")
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            self.documents = []
            self.index = None
    
    def search(self, query, top_k=5):
        """Search for relevant documents"""
        try:
            if not self.index or not self.documents:
                self.load_documents()
            
            if not self.index:
                return []
            
            # Encode query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents) and score > 0.3:  # Threshold for relevance
                    doc = self.documents[idx]
                    results.append({
                        'document': doc,
                        'score': float(score),
                        'text': doc['text'],
                        'sheet': doc['sheet'],
                        'row_data': doc['row_data']
                    })
            
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_context_for_query(self, query, max_length=1000):
        """Get formatted context for AI prompt"""
        results = self.search(query)
        
        if not results:
            return "ไม่พบข้อมูลที่เกี่ยวข้องในระบบ"
        
        context_parts = []
        current_length = 0
        
        for result in results:
            sheet_name = result['sheet']
            row_data = result['row_data']
            
            # Format the context nicely
            context_part = f"จาก {sheet_name}:\n"
            for key, value in row_data.items():
                if value:
                    context_part += f"- {key}: {value}\n"
            context_part += "\n"
            
            if current_length + len(context_part) > max_length:
                break
            
            context_parts.append(context_part)
            current_length += len(context_part)
        
        return "\n".join(context_parts)
    
    def refresh_index(self):
        """Refresh the document index"""
        self.load_documents()
