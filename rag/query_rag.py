"""
RAG Query - Kullanıcı sorusuna göre ilgili schema bilgilerini bul
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.build_vector_db import SchemaVectorDB
from config.db_config import RAG_CONFIG

# Global instance
_vector_db = None

def get_vector_db():
    """Vektör DB singleton"""
    global _vector_db
    if _vector_db is None:
        _vector_db = SchemaVectorDB()
        _vector_db.load(RAG_CONFIG['vector_db_path'])
    return _vector_db

def get_relevant_context(question, top_k=None):
    """
    Kullanıcı sorusuna göre ilgili tablo ve kalıp bilgilerini getir
    """
    if top_k is None:
        top_k = RAG_CONFIG['top_k']
    
    db = get_vector_db()
    results = db.search(question, top_k=top_k)
    
    context_parts = []
    tables_found = set()
    
    for result in results:
        doc = result['document']
        score = result['score']
        meta = result['metadata']
        
        # Sadece yeterince ilgili olanları al (score > 0.3)
        if score > 0.3:
            if meta.get('type') == 'table':
                tables_found.add(meta.get('name'))
            context_parts.append(doc)
    
    context = '\n\n---\n\n'.join(context_parts)
    
    return {
        'context': context,
        'tables': list(tables_found),
        'results': results
    }

def extract_keywords(question):
    """Sorudan anahtar kelimeleri çıkar"""
    # Türkçe stop words
    stop_words = {'bir', 'bu', 'şu', 'o', 'de', 'da', 've', 'ile', 'için', 
                  'mi', 'mı', 'mu', 'mü', 'ne', 'kaç', 'nasıl', 'neden',
                  'hangi', 'kim', 'nerede', 'gibi', 'daha', 'en'}
    
    words = question.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords


if __name__ == '__main__':
    # Test
    test_questions = [
        "Bugün kaç sipariş girildi?",
        "Daikin firmasına bu ay ne kadar ödedik?",
        "Proje listesini göster",
        "2024 ve 2025 yıllarını karşılaştır"
    ]
    
    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Soru: {q}")
        print('='*60)
        
        result = get_relevant_context(q)
        print(f"Bulunan tablolar: {result['tables']}")
        print(f"Context uzunluğu: {len(result['context'])} karakter")
        
        for r in result['results'][:3]:
            print(f"  - Score: {r['score']:.3f} | {r['metadata']}")
