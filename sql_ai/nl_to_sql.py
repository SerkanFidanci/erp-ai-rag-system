"""
Türkçe Doğal Dil → SQL Dönüştürücü
RAG context + Öğrenme sistemi ile zenginleştirilmiş
"""

import requests
import re
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import LLM_CONFIG
from rag.query_rag import get_relevant_context
from learning.feedback_system import (
    get_similar_corrections, 
    format_corrections_for_prompt,
    get_learned_examples,
    format_examples_for_prompt,
    save_correction,
    add_learned_example
)

# Temel sorgu kalıpları (her zaman dahil edilir)
BASE_PATTERNS = """
## ÖNEMLİ KURALLAR

1. Satınalma siparişleri için: TIP = 0 AND EVRAK_KONUSU_ID IN (1, 22, 23, 61)
2. Satış siparişleri için: TIP = 2
3. Tutar hesaplama: SUM(TUTAR * KDV_ORANI / 100 + KDVSIZ_TUTAR - ISKONTO)
4. Firma adı için P.UNVAN kullan (FIRMA_ADI değil!)
5. Tarih karşılaştırması için CAST(TARIH AS DATE) kullan

## JOIN KALIPLARI

Sipariş → Firma:
INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID = S.PARTI_YAMASI_ID
INNER JOIN TOHOM_PARTI P ON P.PARTI_ID = PY.PARTI_ID

Sipariş → Proje:
INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID = S.ILGILI_ID
INNER JOIN TOHOM_PARTI P ON P.PARTI_ID = PY.PARTI_ID

Sipariş → Tutar:
INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR * KDV_ORANI / 100 + KDVSIZ_TUTAR - ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID = S.SIPARIS_ID

## TARİH FONKSİYONLARI
- Bugün: CAST(TARIH AS DATE) = CAST(GETDATE() AS DATE)
- Dün: CAST(TARIH AS DATE) = CAST(GETDATE()-1 AS DATE)
- Bu hafta: TARIH >= DATEADD(day, -7, GETDATE())
- Bu ay: YEAR(TARIH) = YEAR(GETDATE()) AND MONTH(TARIH) = MONTH(GETDATE())
- Bu yıl: YEAR(TARIH) = YEAR(GETDATE())
- Geçen ay: YEAR(TARIH) = YEAR(DATEADD(month, -1, GETDATE())) AND MONTH(TARIH) = MONTH(DATEADD(month, -1, GETDATE()))

## KOLON İSİMLERİ (ÖNEMLİ!)
- Firma adı: P.UNVAN (FIRMA_ADI değil!)
- Sipariş sayısı: COUNT(*) AS SiparisAdedi
- Toplam tutar: SUM(...) AS ToplamTutar
"""

def generate_sql(question):
    """
    Türkçe soruyu SQL'e çevir
    RAG + Öğrenme sistemi ile zenginleştirilmiş
    """
    
    # 1. RAG ile ilgili schema bilgilerini bul
    rag_result = get_relevant_context(question, top_k=5)
    context = rag_result['context']
    
    print(f"RAG bulduğu tablolar: {rag_result['tables']}")
    
    # 2. Öğrenilmiş örnekleri al
    learned_examples = get_learned_examples(limit=5)
    examples_text = format_examples_for_prompt(learned_examples)
    
    # 3. Benzer düzeltmeleri al (ÖNEMLİ!)
    similar_corrections = get_similar_corrections(question, limit=3)
    corrections_text = format_corrections_for_prompt(similar_corrections)
    
    if similar_corrections:
        print(f"Benzer düzeltmeler bulundu: {len(similar_corrections)}")
    
    # 4. Prompt oluştur
    prompt = f"""Sen bir MSSQL veritabanı uzmanısın. Kullanıcının Türkçe sorusunu SQL sorgusuna çevireceksin.

## VERİTABANI BİLGİLERİ

{context}

{BASE_PATTERNS}

{examples_text}

{corrections_text}

---

KULLANICI SORUSU: {question}

---

Yukarıdaki bilgileri ve özellikle DÜZELTMELER bölümünü dikkate alarak SQL sorgusu yaz.
SADECE SQL kodunu yaz. Açıklama yapma, markdown kullanma.
SELECT ile başla:"""

    # 5. LLM'e gönder
    try:
        response = requests.post(
            f"{LLM_CONFIG['base_url']}/api/generate",
            json={
                "model": LLM_CONFIG['model'],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": LLM_CONFIG['temperature'],
                    "num_predict": 800,
                    "num_ctx": 8192
                }
            },
            timeout=LLM_CONFIG['timeout']
        )
        
        if response.status_code == 200:
            result = response.json()
            raw_sql = result.get('response', '').strip()
            return clean_sql(raw_sql)
        else:
            print(f"LLM HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"LLM Error: {e}")
        return None


def learn_from_correction(question, wrong_sql, correct_sql):
    """Kullanıcı düzeltmesinden öğren"""
    save_correction(question, wrong_sql, correct_sql)
    add_learned_example(question, correct_sql)
    print(f"✓ Düzeltme öğrenildi: {question[:50]}...")

def clean_sql(sql):
    """SQL'i temizle ve doğrula"""
    if not sql:
        return None
    
    # Markdown temizle
    sql = sql.replace('```sql', '').replace('```', '')
    
    # SELECT ile başlayan kısmı bul
    lines = []
    started = False
    
    for line in sql.split('\n'):
        line = line.strip()
        if line.upper().startswith('SELECT'):
            started = True
        if started:
            # Açıklama satırlarını atla
            if line.startswith('--') or line.startswith('#'):
                continue
            if line.lower().startswith(('bu sorgu', 'açıklama', 'not:')):
                break
            if line:
                lines.append(line)
    
    if not lines:
        # Alternatif: regex ile bul
        match = re.search(r'SELECT\s+.+', sql, re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r'\s+', ' ', match.group(0)).strip().rstrip(';')
        return None
    
    result = ' '.join(lines)
    result = re.sub(r'\s+', ' ', result).strip().rstrip(';')
    
    return result if result.upper().startswith('SELECT') else None


if __name__ == '__main__':
    # Test
    test_questions = [
        "Bugün kaç sipariş girildi?",
        "Bu ay en çok hangi firmadan alım yaptık?",
        "2024 ve 2025 yıllarını karşılaştır"
    ]
    
    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Soru: {q}")
        sql = generate_sql(q)
        print(f"SQL: {sql}")
