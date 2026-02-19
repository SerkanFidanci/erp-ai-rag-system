"""
SQL Server'dan Schema Bilgilerini Çıkar
Tablolar, kolonlar, ilişkiler ve örnek veriler
"""

import pyodbc
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import get_connection_string

def get_connection():
    """Veritabanı bağlantısı"""
    try:
        return pyodbc.connect(get_connection_string())
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_all_tables(conn):
    """Tüm tabloları listele"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_columns(conn, table_name):
    """Tablo kolonlarını al"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, (table_name,))
    
    columns = []
    for row in cursor.fetchall():
        col = {
            'name': row[0],
            'type': row[1],
            'max_length': row[2],
            'nullable': row[3] == 'YES',
            'default': row[4]
        }
        columns.append(col)
    return columns

def get_primary_keys(conn, table_name):
    """Primary key'leri al"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_NAME = ?
    """, (table_name,))
    return [row[0] for row in cursor.fetchall()]

def get_foreign_keys(conn, table_name):
    """Foreign key'leri al"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COL_NAME(fc.parent_object_id, fc.parent_column_id) AS column_name,
            OBJECT_NAME(fc.referenced_object_id) AS referenced_table,
            COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
        FROM sys.foreign_key_columns fc
        WHERE OBJECT_NAME(fc.parent_object_id) = ?
    """, (table_name,))
    
    fks = []
    for row in cursor.fetchall():
        fks.append({
            'column': row[0],
            'references_table': row[1],
            'references_column': row[2]
        })
    return fks

def get_sample_values(conn, table_name, column_name, limit=5):
    """Kolon için örnek değerler al"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT DISTINCT TOP {limit} [{column_name}]
            FROM [{table_name}]
            WHERE [{column_name}] IS NOT NULL
        """)
        return [str(row[0]) for row in cursor.fetchall()]
    except:
        return []

def get_row_count(conn, table_name):
    """Tablo satır sayısı"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        return cursor.fetchone()[0]
    except:
        return 0

def extract_full_schema(output_path='schema/raw_schema.json'):
    """Tüm veritabanı şemasını çıkar"""
    conn = get_connection()
    if not conn:
        return None
    
    print("Veritabanı şeması çıkarılıyor...")
    
    tables = get_all_tables(conn)
    schema = {'tables': {}}
    
    # Sadece TOHOM_ ile başlayan ana tabloları al (ERP tabloları)
    erp_tables = [t for t in tables if t.startswith('TOHOM_')]
    
    print(f"Toplam {len(erp_tables)} ERP tablosu bulundu")
    
    for i, table_name in enumerate(erp_tables):
        print(f"  [{i+1}/{len(erp_tables)}] {table_name}")
        
        columns = get_table_columns(conn, table_name)
        primary_keys = get_primary_keys(conn, table_name)
        foreign_keys = get_foreign_keys(conn, table_name)
        row_count = get_row_count(conn, table_name)
        
        # Önemli kolonlar için örnek değerler
        sample_columns = ['TIP', 'TUR', 'DURUM', 'CINS']
        samples = {}
        for col in columns:
            if col['name'] in sample_columns or col['name'].endswith('_ID'):
                vals = get_sample_values(conn, table_name, col['name'])
                if vals:
                    samples[col['name']] = vals
        
        schema['tables'][table_name] = {
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'row_count': row_count,
            'sample_values': samples
        }
    
    conn.close()
    
    # JSON olarak kaydet
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    
    print(f"\nŞema kaydedildi: {output_path}")
    return schema

if __name__ == '__main__':
    extract_full_schema()
