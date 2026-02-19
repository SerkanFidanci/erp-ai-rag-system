"""
Fine-tuning için Eğitim Verisi Hazırlama
Qwen2.5-coder modeli için JSONL formatında veri oluşturur
"""

import json
import os
from datetime import datetime

# Eğitim verisi klasörü
TRAINING_DIR = 'training_data'

def ensure_dir():
    os.makedirs(TRAINING_DIR, exist_ok=True)

# ============== VERİTABANI ŞEMASI (Kısa versiyon) ==============

SCHEMA_CONTEXT = """## ERP VERİTABANI

### Tablolar:
- TOHOM_SIPARIS: Siparişler (TIP=0 satınalma, TIP=2 satış)
- TOHOM_SIPARIS_SATIRI: Sipariş kalemleri
- TOHOM_PARTI: Firmalar/Projeler (TUR=5 kurum, TUR=7 proje)
- TOHOM_PARTI_YAMASI: Roller (TUR=6 tedarikçi, TUR=8 müşteri, TUR=17 proje)

### Önemli Kurallar:
- Satınalma: TIP=0 AND EVRAK_KONUSU_ID IN (1,22,23,61)
- Firma adı: P.UNVAN (FIRMA_ADI değil!)
- Tutar: SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO)
- Tarih bugün: CAST(TARIH AS DATE) = CAST(GETDATE() AS DATE)
- Tarih dün: CAST(TARIH AS DATE) = CAST(GETDATE()-1 AS DATE)

### JOIN Kalıpları:
Sipariş→Firma: INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID
Sipariş→Tutar: INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID"""


# ============== ÖRNEK EĞİTİM VERİLERİ ==============

# Bu örnekleri sen genişleteceksin!
SEED_EXAMPLES = [
    # === BUGÜN ===
    {
        "question": "bugün kaç sipariş girildi",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND CAST(TARIH AS DATE)=CAST(GETDATE() AS DATE) AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "bugün kaç adet sipariş var",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND CAST(TARIH AS DATE)=CAST(GETDATE() AS DATE) AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "bugünkü siparişleri listele",
        "sql": "SELECT S.SIPARIS_NO, P.UNVAN AS FirmaAdi, S.TARIH, S.TOPLAM_TUTAR FROM TOHOM_SIPARIS S INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND CAST(S.TARIH AS DATE)=CAST(GETDATE() AS DATE) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) ORDER BY S.TARIH DESC"
    },
    {
        "question": "bugün hangi firmalardan sipariş verdik",
        "sql": "SELECT P.UNVAN AS FirmaAdi, COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS S INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND CAST(S.TARIH AS DATE)=CAST(GETDATE() AS DATE) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY P.UNVAN"
    },
    
    # === DÜN ===
    {
        "question": "dün kaç sipariş girildi",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND CAST(TARIH AS DATE)=CAST(GETDATE()-1 AS DATE) AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "dün hangi firmalardan sipariş verdik",
        "sql": "SELECT P.UNVAN AS FirmaAdi, COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS S INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND CAST(S.TARIH AS DATE)=CAST(GETDATE()-1 AS DATE) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY P.UNVAN"
    },
    {
        "question": "dünkü siparişlerin toplam tutarı",
        "sql": "SELECT SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID WHERE S.TIP=0 AND CAST(S.TARIH AS DATE)=CAST(GETDATE()-1 AS DATE) AND S.EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    
    # === BU HAFTA ===
    {
        "question": "bu hafta kaç sipariş girildi",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND TARIH>=DATEADD(day,-7,GETDATE()) AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "bu hafta hangi firmalardan sipariş verdik",
        "sql": "SELECT P.UNVAN AS FirmaAdi, COUNT(*) AS SiparisAdedi, SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND S.TARIH>=DATEADD(day,-7,GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY P.UNVAN ORDER BY ToplamTutar DESC"
    },
    {
        "question": "son 7 günün sipariş özeti",
        "sql": "SELECT CAST(S.TARIH AS DATE) AS Tarih, COUNT(*) AS SiparisAdedi, SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID WHERE S.TIP=0 AND S.TARIH>=DATEADD(day,-7,GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY CAST(S.TARIH AS DATE) ORDER BY Tarih DESC"
    },
    
    # === BU AY ===
    {
        "question": "bu ay kaç sipariş girildi",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND YEAR(TARIH)=YEAR(GETDATE()) AND MONTH(TARIH)=MONTH(GETDATE()) AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "bu ay toplam ne kadar satınalma yapıldı",
        "sql": "SELECT SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND MONTH(S.TARIH)=MONTH(GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "bu ay en çok hangi firmadan alım yaptık",
        "sql": "SELECT TOP 10 P.UNVAN AS FirmaAdi, COUNT(*) AS SiparisAdedi, SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND MONTH(S.TARIH)=MONTH(GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY P.UNVAN ORDER BY ToplamTutar DESC"
    },
    
    # === BU YIL ===
    {
        "question": "bu yıl kaç sipariş girildi",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND YEAR(TARIH)=YEAR(GETDATE()) AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "bu yıl toplam satınalma tutarı",
        "sql": "SELECT SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "2024 yılında kaç sipariş verildi",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND YEAR(TARIH)=2024 AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    {
        "question": "2025 yılında kaç sipariş verildi",
        "sql": "SELECT COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS WHERE TIP=0 AND YEAR(TARIH)=2025 AND EVRAK_KONUSU_ID IN (1,22,23,61)"
    },
    
    # === YIL KARŞILAŞTIRMA ===
    {
        "question": "2024 ve 2025 yıllarını karşılaştır",
        "sql": "SELECT YEAR(S.TARIH) AS Yil, COUNT(*) AS SiparisAdedi, SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID WHERE S.TIP=0 AND YEAR(S.TARIH) IN (2024,2025) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY YEAR(S.TARIH) ORDER BY Yil"
    },
    {
        "question": "2024 ile 2025 yılının sipariş sayılarını karşılaştır",
        "sql": "SELECT YEAR(S.TARIH) AS Yil, COUNT(*) AS SiparisAdedi, SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID WHERE S.TIP=0 AND YEAR(S.TARIH) IN (2024,2025) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY YEAR(S.TARIH) ORDER BY Yil"
    },
    
    # === FİRMA BAZLI ===
    {
        "question": "Daikin firmasına bu yıl ne kadar ödedik",
        "sql": "SELECT P.UNVAN AS FirmaAdi, COUNT(*) AS SiparisAdedi, SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND P.UNVAN LIKE '%Daikin%' AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY P.UNVAN"
    },
    {
        "question": "Bosch'a bu ay kaç sipariş verdik",
        "sql": "SELECT P.UNVAN AS FirmaAdi, COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS S INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND MONTH(S.TARIH)=MONTH(GETDATE()) AND P.UNVAN LIKE '%Bosch%' AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY P.UNVAN"
    },
    {
        "question": "ABC firmasının siparişlerini listele",
        "sql": "SELECT S.SIPARIS_NO, S.TARIH, SS.TUTAR FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND P.UNVAN LIKE '%ABC%' AND S.EVRAK_KONUSU_ID IN (1,22,23,61) ORDER BY S.TARIH DESC"
    },
    
    # === PROJE ===
    {
        "question": "proje listesi",
        "sql": "SELECT P.UNVAN AS ProjeAdi, PY.PARTI_YAMASI_ID AS ProjeID FROM TOHOM_PARTI P INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_ID=P.PARTI_ID WHERE P.TUR=7 AND PY.TUR=17 ORDER BY P.UNVAN"
    },
    {
        "question": "projeleri göster",
        "sql": "SELECT P.UNVAN AS ProjeAdi, PY.PARTI_YAMASI_ID AS ProjeID FROM TOHOM_PARTI P INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_ID=P.PARTI_ID WHERE P.TUR=7 AND PY.TUR=17 ORDER BY P.UNVAN"
    },
    {
        "question": "hangi projeler var",
        "sql": "SELECT P.UNVAN AS ProjeAdi, PY.PARTI_YAMASI_ID AS ProjeID FROM TOHOM_PARTI P INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_ID=P.PARTI_ID WHERE P.TUR=7 AND PY.TUR=17 ORDER BY P.UNVAN"
    },
    
    # === TEDARİKÇİ ===
    {
        "question": "tedarikçi listesi",
        "sql": "SELECT DISTINCT P.UNVAN AS TedarikciAdi FROM TOHOM_PARTI P INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_ID=P.PARTI_ID WHERE PY.TUR=6 ORDER BY P.UNVAN"
    },
    {
        "question": "firma listesi",
        "sql": "SELECT DISTINCT P.UNVAN AS FirmaAdi FROM TOHOM_PARTI P INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_ID=P.PARTI_ID WHERE PY.TUR=6 ORDER BY P.UNVAN"
    },
    
    # === TOP LİSTELER ===
    {
        "question": "en yüksek tutarlı 10 sipariş",
        "sql": "SELECT TOP 10 S.SIPARIS_NO, P.UNVAN AS FirmaAdi, S.TARIH, SS.TUTAR FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) ORDER BY SS.TUTAR DESC"
    },
    {
        "question": "en çok sipariş verilen 5 firma",
        "sql": "SELECT TOP 5 P.UNVAN AS FirmaAdi, COUNT(*) AS SiparisAdedi FROM TOHOM_SIPARIS S INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID=S.PARTI_YAMASI_ID INNER JOIN TOHOM_PARTI P ON P.PARTI_ID=PY.PARTI_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY P.UNVAN ORDER BY SiparisAdedi DESC"
    },
    
    # === AYLIK ÖZET ===
    {
        "question": "bu yılın aylık sipariş özeti",
        "sql": "SELECT MONTH(S.TARIH) AS Ay, COUNT(*) AS SiparisAdedi, SUM(SS.TUTAR) AS ToplamTutar FROM TOHOM_SIPARIS S INNER JOIN (SELECT SIPARIS_ID, SUM(TUTAR*KDV_ORANI/100+KDVSIZ_TUTAR-ISKONTO) AS TUTAR FROM TOHOM_SIPARIS_SATIRI GROUP BY SIPARIS_ID) SS ON SS.SIPARIS_ID=S.SIPARIS_ID WHERE S.TIP=0 AND YEAR(S.TARIH)=YEAR(GETDATE()) AND S.EVRAK_KONUSU_ID IN (1,22,23,61) GROUP BY MONTH(S.TARIH) ORDER BY Ay"
    },
]


def create_training_example(question, sql):
    """Tek bir eğitim örneği oluştur (Qwen chat formatı)"""
    return {
        "messages": [
            {
                "role": "system",
                "content": f"Sen bir MSSQL veritabanı uzmanısın. Kullanıcının Türkçe sorusunu SQL sorgusuna çeviriyorsun.\n\n{SCHEMA_CONTEXT}\n\nKurallar:\n- SADECE SQL yaz, açıklama yapma\n- SELECT ile başla\n- Firma adı için P.UNVAN kullan"
            },
            {
                "role": "user", 
                "content": question
            },
            {
                "role": "assistant",
                "content": sql
            }
        ]
    }


def load_corrections():
    """Kullanıcı düzeltmelerini yükle"""
    corrections_file = 'data/corrections.json'
    if os.path.exists(corrections_file):
        with open(corrections_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def load_learned_examples():
    """Başarılı örnekleri yükle"""
    examples_file = 'data/learned_examples.json'
    if os.path.exists(examples_file):
        with open(examples_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def generate_training_data():
    """Tüm eğitim verisini oluştur"""
    ensure_dir()
    
    all_examples = []
    
    # 1. Seed örnekler
    print(f"1. Seed örnekler ekleniyor: {len(SEED_EXAMPLES)}")
    for ex in SEED_EXAMPLES:
        all_examples.append(create_training_example(ex['question'], ex['sql']))
    
    # 2. Kullanıcı düzeltmeleri
    corrections = load_corrections()
    print(f"2. Kullanıcı düzeltmeleri ekleniyor: {len(corrections)}")
    for corr in corrections:
        all_examples.append(create_training_example(corr['question'], corr['correct_sql']))
    
    # 3. Başarılı örnekler
    learned = load_learned_examples()
    print(f"3. Başarılı örnekler ekleniyor: {len(learned)}")
    for ex in learned:
        all_examples.append(create_training_example(ex['question'], ex['sql']))
    
    # Benzersiz örnekleri filtrele
    seen = set()
    unique_examples = []
    for ex in all_examples:
        key = ex['messages'][1]['content'].lower()  # question
        if key not in seen:
            seen.add(key)
            unique_examples.append(ex)
    
    print(f"\nToplam benzersiz örnek: {len(unique_examples)}")
    
    # JSONL formatında kaydet
    output_file = os.path.join(TRAINING_DIR, 'train.jsonl')
    with open(output_file, 'w', encoding='utf-8') as f:
        for ex in unique_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    print(f"Eğitim verisi kaydedildi: {output_file}")
    
    # İstatistikler
    stats = {
        'total_examples': len(unique_examples),
        'seed_examples': len(SEED_EXAMPLES),
        'corrections': len(corrections),
        'learned': len(learned),
        'generated_at': datetime.now().isoformat()
    }
    
    with open(os.path.join(TRAINING_DIR, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    return unique_examples


def add_custom_example(question, sql):
    """Manuel örnek ekle"""
    custom_file = os.path.join(TRAINING_DIR, 'custom_examples.json')
    
    if os.path.exists(custom_file):
        with open(custom_file, 'r', encoding='utf-8') as f:
            examples = json.load(f)
    else:
        examples = []
    
    examples.append({
        'question': question,
        'sql': sql,
        'added_at': datetime.now().isoformat()
    })
    
    ensure_dir()
    with open(custom_file, 'w', encoding='utf-8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)
    
    print(f"Örnek eklendi. Toplam: {len(examples)}")


if __name__ == '__main__':
    print("="*60)
    print("   Fine-tuning Eğitim Verisi Oluşturucu")
    print("="*60)
    generate_training_data()
