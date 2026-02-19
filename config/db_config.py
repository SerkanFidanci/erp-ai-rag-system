"""
Veritabanı ve LLM Konfigürasyonu
"""

import os


def _int_env(name, default):
    """Integer environment değişkeni oku."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name, default):
    """Float environment değişkeni oku."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


# SQL Server Bağlantı Ayarları
DB_CONFIG = {
    'server': os.getenv('ERP_DB_SERVER', 'localhost'),
    'database': os.getenv('ERP_DB_NAME', 'YOUR_DATABASE'),
    'username': os.getenv('ERP_DB_USER', 'sa'),
    'password': os.getenv('ERP_DB_PASSWORD', 'YOUR_PASSWORD'),
    'driver': os.getenv('ERP_DB_DRIVER', 'ODBC Driver 17 for SQL Server')
}

# Ollama Ayarları
LLM_CONFIG = {
    'base_url': os.getenv('ERP_LLM_BASE_URL', 'http://localhost:11434'),
    'model': os.getenv('ERP_LLM_MODEL', 'qwen2.5-coder:7b'),
    'temperature': _float_env('ERP_LLM_TEMPERATURE', 0.1),
    'timeout': _int_env('ERP_LLM_TIMEOUT', 120)
}

# RAG Ayarları
RAG_CONFIG = {
    'chunk_size': _int_env('ERP_RAG_CHUNK_SIZE', 500),
    'chunk_overlap': _int_env('ERP_RAG_CHUNK_OVERLAP', 50),
    'top_k': _int_env('ERP_RAG_TOP_K', 5),  # En ilgili 5 tablo bilgisi
    'vector_db_path': os.getenv('ERP_RAG_VECTOR_DB_PATH', './data/vector_db')
}

# Güvenlik Ayarları
SECURITY_CONFIG = {
    'allowed_operations': ['SELECT'],
    'blocked_keywords': ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC'],
    'max_results': _int_env('ERP_MAX_RESULTS', 1000)
}


def get_connection_string():
    return (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
