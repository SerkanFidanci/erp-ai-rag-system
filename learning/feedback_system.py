"""
Öğrenme Sistemi - Feedback ve Düzeltmeler
Kullanıcı düzeltmelerini kaydeder ve sonraki sorgularda kullanır
"""

import json
import os
from datetime import datetime

FEEDBACK_FILE = 'data/feedback.json'
CORRECTIONS_FILE = 'data/corrections.json'

def ensure_data_dir():
    """Data klasörünü oluştur"""
    os.makedirs('data', exist_ok=True)

def load_json(filepath):
    """JSON dosyasını yükle"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(filepath, data):
    """JSON dosyasına kaydet"""
    ensure_data_dir()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============== DÜZELTME SİSTEMİ ==============

def save_correction(question, wrong_sql, correct_sql, explanation=None):
    """
    Kullanıcının düzeltmesini kaydet
    Bu düzeltmeler sonraki sorgularda örnek olarak kullanılacak
    """
    corrections = load_json(CORRECTIONS_FILE)
    
    correction = {
        'id': len(corrections) + 1,
        'timestamp': datetime.now().isoformat(),
        'question': question,
        'wrong_sql': wrong_sql,
        'correct_sql': correct_sql,
        'explanation': explanation,
        'used_count': 0  # Kaç kez örnek olarak kullanıldı
    }
    
    corrections.append(correction)
    save_json(CORRECTIONS_FILE, corrections)
    
    print(f"✓ Düzeltme kaydedildi (ID: {correction['id']})")
    return correction

def get_similar_corrections(question, limit=3):
    """
    Soruya benzer düzeltmeleri bul
    Basit keyword matching kullanıyoruz, ileride embedding ile geliştirilebilir
    """
    corrections = load_json(CORRECTIONS_FILE)
    
    if not corrections:
        return []
    
    question_lower = question.lower()
    question_words = set(question_lower.split())
    
    scored = []
    for corr in corrections:
        corr_words = set(corr['question'].lower().split())
        # Ortak kelime sayısı
        common = len(question_words & corr_words)
        if common > 0:
            scored.append((common, corr))
    
    # En yüksek skorlu düzeltmeleri döndür
    scored.sort(key=lambda x: x[0], reverse=True)
    return [corr for _, corr in scored[:limit]]

def get_all_corrections():
    """Tüm düzeltmeleri getir"""
    return load_json(CORRECTIONS_FILE)

def format_corrections_for_prompt(corrections):
    """
    Düzeltmeleri LLM prompt'una eklenecek formata çevir
    """
    if not corrections:
        return ""
    
    lines = ["## DAHA ÖNCE YAPILAN DÜZELTMELER (Bunlara dikkat et!)"]
    
    for corr in corrections:
        lines.append(f"""
Soru: {corr['question']}
YANLIŞ: {corr['wrong_sql']}
DOĞRU: {corr['correct_sql']}
""")
    
    return '\n'.join(lines)

# ============== FEEDBACK SİSTEMİ ==============

def save_feedback(question, sql, is_correct, user_comment=None):
    """
    Kullanıcı geri bildirimini kaydet
    """
    feedbacks = load_json(FEEDBACK_FILE)
    
    feedback = {
        'id': len(feedbacks) + 1,
        'timestamp': datetime.now().isoformat(),
        'question': question,
        'sql': sql,
        'is_correct': is_correct,
        'user_comment': user_comment
    }
    
    feedbacks.append(feedback)
    save_json(FEEDBACK_FILE, feedbacks)
    
    return feedback

def get_feedback_stats():
    """Feedback istatistikleri"""
    feedbacks = load_json(FEEDBACK_FILE)
    
    total = len(feedbacks)
    correct = sum(1 for f in feedbacks if f['is_correct'])
    
    return {
        'total': total,
        'correct': correct,
        'incorrect': total - correct,
        'accuracy': (correct / total * 100) if total > 0 else 0
    }

# ============== ÖRNEK SORGU YÖNETİMİ ==============

EXAMPLES_FILE = 'data/learned_examples.json'

def add_learned_example(question, sql, description=None):
    """
    Başarılı bir sorguyu örnek olarak kaydet
    """
    examples = load_json(EXAMPLES_FILE)
    
    # Aynı soru zaten var mı?
    for ex in examples:
        if ex['question'].lower() == question.lower():
            ex['sql'] = sql  # Güncelle
            ex['updated_at'] = datetime.now().isoformat()
            save_json(EXAMPLES_FILE, examples)
            return ex
    
    example = {
        'id': len(examples) + 1,
        'question': question,
        'sql': sql,
        'description': description,
        'created_at': datetime.now().isoformat(),
        'success_count': 1
    }
    
    examples.append(example)
    save_json(EXAMPLES_FILE, examples)
    
    return example

def get_learned_examples(limit=10):
    """Öğrenilmiş örnekleri getir"""
    examples = load_json(EXAMPLES_FILE)
    # En çok başarılı olanları önce
    examples.sort(key=lambda x: x.get('success_count', 0), reverse=True)
    return examples[:limit]

def format_examples_for_prompt(examples):
    """Örnekleri prompt formatına çevir"""
    if not examples:
        return ""
    
    lines = ["## ÖĞRENİLMİŞ BAŞARILI SORGULAR"]
    
    for ex in examples:
        lines.append(f"""
Soru: {ex['question']}
SQL: {ex['sql']}
""")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    # Test
    print("Test: Düzeltme kaydet")
    save_correction(
        question="dün kaç sipariş girildi",
        wrong_sql="SELECT COUNT(*) FROM TOHOM_SIPARIS WHERE TARIH = GETDATE()-1",
        correct_sql="SELECT COUNT(*) AS SiparisAdedi, P.UNVAN AS FirmaAdi FROM TOHOM_SIPARIS S INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID = S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID = PY.PARTI_ID WHERE CAST(S.TARIH AS DATE) = CAST(GETDATE()-1 AS DATE) GROUP BY P.UNVAN",
        explanation="FIRMA_ADI değil P.UNVAN kullanılmalı"
    )
    
    print("\nTest: Benzer düzeltmeleri bul")
    similar = get_similar_corrections("bugün kaç sipariş var")
    for s in similar:
        print(f"  - {s['question']}")
