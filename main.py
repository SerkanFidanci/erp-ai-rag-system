"""
ERP AI RAG - Ana Program
Kurulum ve başlatma
"""

import os
import sys

def check_requirements():
    """Gerekli kütüphaneleri kontrol et"""
    required = ['flask', 'pyodbc', 'requests', 'sentence_transformers', 'numpy']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print("Eksik kütüphaneler:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nKurulum: pip install -r requirements.txt")
        return False
    
    return True

def check_ollama():
    """Ollama'yı kontrol et"""
    import requests
    from config.db_config import LLM_CONFIG
    
    try:
        response = requests.get(f"{LLM_CONFIG['base_url']}/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            if LLM_CONFIG['model'] in models or any(LLM_CONFIG['model'] in m for m in models):
                print(f"✓ Ollama çalışıyor, model: {LLM_CONFIG['model']}")
                return True
            else:
                print(f"✗ Model bulunamadı: {LLM_CONFIG['model']}")
                print(f"  Mevcut modeller: {models}")
                print(f"  Kurulum: ollama pull {LLM_CONFIG['model']}")
                return False
    except:
        pass
    
    print("✗ Ollama çalışmıyor")
    print("  Başlatmak için: ollama serve")
    return False

def check_database():
    """Veritabanı bağlantısını kontrol et"""
    from sql_ai.run_sql import get_connection
    
    conn = get_connection()
    if conn:
        conn.close()
        print("✓ Veritabanı bağlantısı başarılı")
        return True
    
    print("✗ Veritabanı bağlantısı başarısız")
    print("  config/db_config.py dosyasını kontrol edin")
    return False

def check_rag():
    """RAG vektör DB'yi kontrol et"""
    if os.path.exists('data/vector_db/embeddings.npy'):
        print("✓ RAG vektör veritabanı mevcut")
        return True
    
    print("✗ RAG vektör veritabanı bulunamadı")
    print("  Oluşturmak için: python setup.py")
    return False

def setup_rag():
    """RAG sistemini kur"""
    print("\n" + "="*60)
    print("RAG Sistemi Kurulumu")
    print("="*60)
    
    # 1. Schema çıkar
    print("\n1. Veritabanı şeması çıkarılıyor...")
    from schema.extract_schema import extract_full_schema
    extract_full_schema()
    
    # 2. Schema temizle
    print("\n2. Schema AI için optimize ediliyor...")
    from schema.clean_schema import clean_schema
    clean_schema()
    
    # 3. Vektör DB oluştur
    print("\n3. Vektör veritabanı oluşturuluyor...")
    from rag.build_vector_db import build_vector_db
    build_vector_db()
    
    print("\n✓ RAG sistemi kuruldu!")

def run_server():
    """Flask sunucusunu başlat"""
    print("\n" + "="*60)
    print("   ERP AI RAG - Sunucu Başlatılıyor")
    print("="*60)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    from api.app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

def main():
    """Ana fonksiyon"""
    print("="*60)
    print("   ERP AI RAG - Akıllı Veritabanı Asistanı")
    print("="*60)
    
    # Çalışma dizinine git
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'setup':
            # Tam kurulum
            if not check_requirements():
                return
            if not check_database():
                return
            setup_rag()
            
        elif command == 'run':
            # Sunucuyu başlat
            if not check_requirements():
                return
            run_server()
            
        elif command == 'check':
            # Sistem kontrolü
            print("\nSistem Kontrolü:")
            print("-"*40)
            check_requirements()
            check_ollama()
            check_database()
            check_rag()
            
        else:
            print(f"Bilinmeyen komut: {command}")
            print_usage()
    else:
        print_usage()

def print_usage():
    """Kullanım bilgisi"""
    print("""
Kullanım:
    python main.py setup    - RAG sistemini kur (ilk kurulum)
    python main.py run      - Sunucuyu başlat
    python main.py check    - Sistem kontrolü

İlk Kurulum Adımları:
    1. config/db_config.py dosyasını düzenle
    2. Ollama'yı başlat: ollama serve
    3. Model kur: ollama pull qwen2.5-coder:7b
    4. RAG kur: python main.py setup
    5. Başlat: python main.py run
    """)

if __name__ == '__main__':
    main()
