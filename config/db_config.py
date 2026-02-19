"""
Veritabanı ve LLM Konfigürasyonu
"""

# SQL Server Bağlantı Ayarları
DB_CONFIG = {
    'server': 'localhost',
    'database': 'YOUR_DATABASE',
    'username': 'sa',
    'password': 'YOUR_PASSWORD',
    'driver': 'ODBC Driver 17 for SQL Server'
}

# Ollama Ayarları
LLM_CONFIG = {
    'base_url': 'http://localhost:11434',
    'model': 'qwen2.5-coder:7b',
    'temperature': 0.1,
    'timeout': 120
}

# RAG Ayarları
RAG_CONFIG = {
    'chunk_size': 500,
    'chunk_overlap': 50,
    'top_k': 5,  # En ilgili 5 tablo bilgisi
    'vector_db_path': './data/vector_db'
}

# Güvenlik Ayarları
SECURITY_CONFIG = {
    'allowed_operations': ['SELECT'],
    'blocked_keywords': ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC'],
    'max_results': 1000
}

def get_connection_string():
    return (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
