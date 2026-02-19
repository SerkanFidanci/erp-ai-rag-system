"""
SQL Güvenlik Kontrolü
Zararlı sorguları engelle
"""

import re
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import SECURITY_CONFIG

class SQLValidator:
    def __init__(self):
        self.allowed_ops = SECURITY_CONFIG['allowed_operations']
        self.blocked_keywords = SECURITY_CONFIG['blocked_keywords']
    
    def validate(self, sql):
        """
        SQL sorgusunu doğrula
        Returns: (is_valid, error_message)
        """
        if not sql:
            return False, "SQL sorgusu boş"
        
        sql_upper = sql.upper().strip()
        
        # 1. Sadece izin verilen operasyonlar
        first_word = sql_upper.split()[0] if sql_upper.split() else ''
        if first_word not in self.allowed_ops:
            return False, f"Sadece {', '.join(self.allowed_ops)} sorguları çalıştırılabilir"
        
        # 2. Yasaklı kelimeler
        for keyword in self.blocked_keywords:
            # Kelime sınırlarını kontrol et
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Güvenlik: '{keyword}' kullanılamaz"
        
        # 3. Çoklu statement kontrolü (SQL injection)
        if ';' in sql:
            # Sadece sondaki ; kabul edilebilir
            if sql.rstrip(';').count(';') > 0:
                return False, "Çoklu SQL ifadesi tespit edildi"
        
        # 4. Yorum içinde gizli komut kontrolü
        if '--' in sql or '/*' in sql:
            return False, "SQL yorumları kullanılamaz"
        
        # 5. xp_cmdshell gibi tehlikeli fonksiyonlar
        dangerous_funcs = ['xp_cmdshell', 'sp_execute', 'exec(', 'execute(']
        for func in dangerous_funcs:
            if func.lower() in sql.lower():
                return False, f"Güvenlik: '{func}' kullanılamaz"
        
        return True, None
    
    def sanitize(self, sql):
        """SQL'i temizle"""
        if not sql:
            return None
        
        # Sondaki ; kaldır
        sql = sql.rstrip(';').strip()
        
        # Çift boşlukları tek boşluğa çevir
        sql = re.sub(r'\s+', ' ', sql)
        
        return sql


# Singleton instance
_validator = SQLValidator()

def validate_sql(sql):
    """SQL doğrula"""
    return _validator.validate(sql)

def sanitize_sql(sql):
    """SQL temizle"""
    return _validator.sanitize(sql)


if __name__ == '__main__':
    # Test
    test_cases = [
        "SELECT * FROM users",
        "DROP TABLE users",
        "SELECT * FROM users; DELETE FROM users",
        "SELECT * FROM users WHERE name = 'test' -- comment",
        "UPDATE users SET name = 'x'",
        "SELECT * FROM TOHOM_SIPARIS WHERE TIP = 0"
    ]
    
    for sql in test_cases:
        is_valid, error = validate_sql(sql)
        status = "✓" if is_valid else "✗"
        print(f"{status} {sql[:50]}...")
        if error:
            print(f"   Hata: {error}")
