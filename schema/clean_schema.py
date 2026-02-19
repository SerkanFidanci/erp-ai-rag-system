"""
Schema'yı AI için Optimize Et
Her tablo için okunabilir döküman oluştur
"""

import json
import os

# Önemli ERP tabloları ve açıklamaları
TABLE_DESCRIPTIONS = {
    'TOHOM_SIPARIS': 'Satınalma ve satış siparişleri. TIP=0 satınalma, TIP=2 satış.',
    'TOHOM_SIPARIS_SATIRI': 'Sipariş kalemleri/satırları. Miktar, fiyat, tutar bilgileri.',
    'TOHOM_PARTI': 'Firmalar, kişiler, projeler. TUR=5 kurum, TUR=7 proje.',
    'TOHOM_PARTI_YAMASI': 'Parti rolleri. TUR=6 tedarikçi, TUR=8 müşteri, TUR=17 proje.',
    'TOHOM_CARI_KART': 'Cari hesap kartları, ticari bilgiler.',
    'TOHOM_CARI_HAREKET': 'Cari hesap hareketleri.',
    'TOHOM_FATURA': 'Faturalar.',
    'TOHOM_FATURA_SATIRI': 'Fatura kalemleri.',
    'TOHOM_EVRAK_KONUSU': 'Evrak türleri. 1=Satınalma Sipariş, 22=Taşeron Sözleşme, 23=Satınalma Sözleşme, 61=Sözleşmesiz Hizmet.',
    'TOHOM_DEPO_FISI': 'Depo giriş/çıkış fişleri.',
    'TOHOM_DEPO_FISI_SATIRI': 'Depo fişi kalemleri.',
    'TOHOM_URUN': 'Ürün/malzeme tanımları.',
    'TOHOM_PROJE': 'Proje tanımları.',
    'TOHOM_HESAP_HAREKETI': 'Muhasebe hesap hareketleri.',
    'TOHOM_AKTIVITE': 'İş aktiviteleri.',
    'TOHOM_PERSONEL': 'Personel bilgileri.'
}

# Önemli kolon açıklamaları
COLUMN_DESCRIPTIONS = {
    'PARTI_YAMASI_ID': 'Firma/müşteri/tedarikçi bağlantısı',
    'ILGILI_ID': 'İlgili proje bağlantısı (PARTI_YAMASI_ID)',
    'TIP': 'Kayıt tipi (0=satınalma, 2=satış vb.)',
    'TUR': 'Kayıt türü',
    'EVRAK_KONUSU_ID': 'Evrak türü (1,22,23,61=satınalma)',
    'TARIH': 'İşlem tarihi',
    'TOPLAM_TUTAR': 'Toplam tutar',
    'TUTAR': 'Tutar',
    'KDVSIZ_TUTAR': 'KDV hariç tutar',
    'KDV_ORANI': 'KDV oranı (%)',
    'ISKONTO': 'İskonto tutarı',
    'MIKTAR': 'Miktar',
    'BIRIM_FIYATI': 'Birim fiyat',
    'UNVAN': 'Firma/proje adı',
    'KOD': 'Kod',
    'SIPARIS_NO': 'Sipariş numarası'
}

def clean_schema(input_path='schema/raw_schema.json', output_dir='schema/tables'):
    """Her tablo için ayrı döküman oluştur"""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_docs = []
    
    for table_name, table_info in schema['tables'].items():
        doc = create_table_document(table_name, table_info)
        all_docs.append(doc)
        
        # Her tablo için ayrı dosya
        file_path = os.path.join(output_dir, f"{table_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(doc)
    
    # Tüm tabloları tek dosyada birleştir
    with open('schema/schema.txt', 'w', encoding='utf-8') as f:
        f.write('\n\n---\n\n'.join(all_docs))
    
    # Önemli ilişkileri ve sorgu kalıplarını ekle
    write_query_patterns()
    
    print(f"{len(all_docs)} tablo dökümantasyonu oluşturuldu")

def create_table_document(table_name, table_info):
    """Tek tablo için AI-friendly döküman"""
    
    lines = []
    
    # Tablo başlığı
    lines.append(f"# {table_name}")
    
    # Açıklama
    if table_name in TABLE_DESCRIPTIONS:
        lines.append(f"Açıklama: {TABLE_DESCRIPTIONS[table_name]}")
    
    # Satır sayısı
    lines.append(f"Kayıt sayısı: {table_info['row_count']:,}")
    
    # Primary Key
    if table_info['primary_keys']:
        lines.append(f"Primary Key: {', '.join(table_info['primary_keys'])}")
    
    # Kolonlar
    lines.append("\n## Kolonlar")
    for col in table_info['columns']:
        col_line = f"- {col['name']} ({col['type']}"
        if col['max_length']:
            col_line += f", max:{col['max_length']}"
        col_line += ")"
        
        # Kolon açıklaması
        if col['name'] in COLUMN_DESCRIPTIONS:
            col_line += f" → {COLUMN_DESCRIPTIONS[col['name']]}"
        
        lines.append(col_line)
    
    # Foreign Keys
    if table_info['foreign_keys']:
        lines.append("\n## İlişkiler")
        for fk in table_info['foreign_keys']:
            lines.append(f"- {fk['column']} → {fk['references_table']}.{fk['references_column']}")
    
    # Örnek değerler
    if table_info['sample_values']:
        lines.append("\n## Örnek Değerler")
        for col, values in table_info['sample_values'].items():
            lines.append(f"- {col}: {', '.join(values[:5])}")
    
    return '\n'.join(lines)

def write_query_patterns():
    """Sık kullanılan sorgu kalıplarını yaz"""
    
    patterns = """
# SORGU KALIPLARI

## Sipariş → Firma Bağlantısı
```sql
SELECT S.*, P.UNVAN as FIRMA_ADI
FROM TOHOM_SIPARIS S
INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID = S.PARTI_YAMASI_ID
INNER JOIN TOHOM_PARTI P ON P.PARTI_ID = PY.PARTI_ID
```

## Sipariş → Proje Bağlantısı
```sql
SELECT S.*, P.UNVAN as PROJE_ADI
FROM TOHOM_SIPARIS S
INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_YAMASI_ID = S.ILGILI_ID
INNER JOIN TOHOM_PARTI P ON P.PARTI_ID = PY.PARTI_ID
```

## Sipariş Tutarı Hesaplama (Satırlardan)
```sql
SELECT S.SIPARIS_ID, SUM(SS.TUTAR * SS.KDV_ORANI / 100 + SS.KDVSIZ_TUTAR - SS.ISKONTO) as TOPLAM
FROM TOHOM_SIPARIS S
INNER JOIN TOHOM_SIPARIS_SATIRI SS ON SS.SIPARIS_ID = S.SIPARIS_ID
GROUP BY S.SIPARIS_ID
```

## Satınalma Filtresi
```sql
WHERE TIP = 0 AND EVRAK_KONUSU_ID IN (1, 22, 23, 61)
```

## Satış Filtresi
```sql
WHERE TIP = 2
```

## Proje Listesi
```sql
SELECT P.UNVAN, PY.PARTI_YAMASI_ID
FROM TOHOM_PARTI P
INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_ID = P.PARTI_ID
WHERE P.TUR = 7 AND PY.TUR = 17
```

## Tedarikçi Listesi
```sql
SELECT DISTINCT P.UNVAN
FROM TOHOM_PARTI P
INNER JOIN TOHOM_PARTI_YAMASI PY ON PY.PARTI_ID = P.PARTI_ID
WHERE PY.TUR = 6
```

## Tarih Filtreleri
- Bugün: CAST(TARIH AS DATE) = CAST(GETDATE() AS DATE)
- Bu hafta: TARIH >= DATEADD(day, -7, GETDATE())
- Bu ay: YEAR(TARIH) = YEAR(GETDATE()) AND MONTH(TARIH) = MONTH(GETDATE())
- Bu yıl: YEAR(TARIH) = YEAR(GETDATE())
- Belirli yıl: YEAR(TARIH) = 2025
"""
    
    with open('schema/query_patterns.txt', 'w', encoding='utf-8') as f:
        f.write(patterns)

if __name__ == '__main__':
    clean_schema()
