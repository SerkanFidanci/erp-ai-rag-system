"""
SQL Sorgusunu Çalıştır
"""

import pyodbc
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_connection_string, SECURITY_CONFIG
from sql_ai.sql_validator import validate_sql, sanitize_sql

def get_connection():
    """Veritabanı bağlantısı"""
    try:
        return pyodbc.connect(get_connection_string())
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def run_query(sql):
    """
    SQL sorgusunu çalıştır
    Returns: (results, columns, error)
    """
    
    # 1. Güvenlik kontrolü
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return None, None, error
    
    # 2. SQL'i temizle
    sql = sanitize_sql(sql)
    
    # 3. Bağlantı kur
    conn = get_connection()
    if not conn:
        return None, None, "Veritabanına bağlanılamadı"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Kolon isimleri
        columns = [column[0] for column in cursor.description]
        
        # Sonuçları al (max limit)
        rows = cursor.fetchmany(SECURITY_CONFIG['max_results'])
        
        # Dict listesine çevir
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results, columns, None
        
    except Exception as e:
        conn.close()
        return None, None, str(e)

def format_results(results, columns):
    """Sonuçları tablo formatında göster"""
    if not results:
        return "Sonuç bulunamadı."
    
    # Kolon genişlikleri
    widths = {col: len(col) for col in columns}
    for row in results[:20]:
        for col in columns:
            val = str(row.get(col, ''))[:50]
            widths[col] = max(widths[col], len(val))
    
    # Header
    header = ' | '.join(col.ljust(widths[col]) for col in columns)
    separator = '-+-'.join('-' * widths[col] for col in columns)
    
    lines = [header, separator]
    
    # Rows
    for row in results[:20]:
        row_str = ' | '.join(
            str(row.get(col, ''))[:50].ljust(widths[col]) 
            for col in columns
        )
        lines.append(row_str)
    
    if len(results) > 20:
        lines.append(f"... ve {len(results) - 20} satır daha")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    # Test
    sql = "SELECT TOP 5 SIPARIS_NO, TARIH, TOPLAM_TUTAR FROM TOHOM_SIPARIS ORDER BY TARIH DESC"
    
    results, columns, error = run_query(sql)
    
    if error:
        print(f"Hata: {error}")
    else:
        print(format_results(results, columns))
