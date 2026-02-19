"""
RAG Vector Database Oluştur
Schema bilgilerini vektör veritabanına yükle
"""

import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle

class SchemaVectorDB:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Embedding modeli yükle
        all-MiniLM-L6-v2: Hızlı ve etkili, Türkçe için de iyi
        """
        print(f"Embedding modeli yükleniyor: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = None
        self.metadata = []
    
    def add_documents(self, docs, metadata_list=None):
        """Dökümanları ekle"""
        self.documents.extend(docs)
        if metadata_list:
            self.metadata.extend(metadata_list)
        else:
            self.metadata.extend([{}] * len(docs))
    
    def build_index(self):
        """Vektör indeksini oluştur"""
        print(f"{len(self.documents)} döküman için embedding oluşturuluyor...")
        self.embeddings = self.model.encode(self.documents, show_progress_bar=True)
        print("İndeks oluşturuldu")
    
    def search(self, query, top_k=5):
        """Sorguya en benzer dökümanları bul"""
        query_embedding = self.model.encode([query])[0]
        
        # Cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # En yüksek skorlu indeksleri al
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'document': self.documents[idx],
                'score': float(similarities[idx]),
                'metadata': self.metadata[idx]
            })
        
        return results
    
    def save(self, path='data/vector_db'):
        """Veritabanını kaydet"""
        os.makedirs(path, exist_ok=True)
        
        with open(os.path.join(path, 'documents.pkl'), 'wb') as f:
            pickle.dump(self.documents, f)
        
        with open(os.path.join(path, 'metadata.pkl'), 'wb') as f:
            pickle.dump(self.metadata, f)
        
        np.save(os.path.join(path, 'embeddings.npy'), self.embeddings)
        
        print(f"Veritabanı kaydedildi: {path}")
    
    def load(self, path='data/vector_db'):
        """Veritabanını yükle"""
        with open(os.path.join(path, 'documents.pkl'), 'rb') as f:
            self.documents = pickle.load(f)
        
        with open(os.path.join(path, 'metadata.pkl'), 'rb') as f:
            self.metadata = pickle.load(f)
        
        self.embeddings = np.load(os.path.join(path, 'embeddings.npy'))
        
        print(f"Veritabanı yüklendi: {len(self.documents)} döküman")


def build_vector_db():
    """Schema dosyalarından vektör DB oluştur"""
    
    db = SchemaVectorDB()
    
    # 1. Tablo dökümanlarını yükle
    tables_dir = 'schema/tables'
    if os.path.exists(tables_dir):
        for filename in os.listdir(tables_dir):
            if filename.endswith('.txt'):
                table_name = filename.replace('.txt', '')
                filepath = os.path.join(tables_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                db.add_documents(
                    [content],
                    [{'type': 'table', 'name': table_name}]
                )
    
    # 2. Sorgu kalıplarını yükle
    patterns_file = 'schema/query_patterns.txt'
    if os.path.exists(patterns_file):
        with open(patterns_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Her kalıbı ayrı döküman olarak ekle
        patterns = content.split('##')
        for pattern in patterns:
            if pattern.strip():
                db.add_documents(
                    [pattern.strip()],
                    [{'type': 'pattern'}]
                )
    
    # 3. İndeks oluştur ve kaydet
    db.build_index()
    db.save()
    
    return db


if __name__ == '__main__':
    build_vector_db()
