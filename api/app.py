"""
ERP AI RAG - Flask API
"""

from flask import Flask, render_template, request, jsonify
import os
import sys

# Path ayarları
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config.db_config import LLM_CONFIG
from sql_ai.nl_to_sql import generate_sql, learn_from_correction
from sql_ai.run_sql import run_query
from sql_ai.sql_validator import validate_sql
from learning.feedback_system import save_feedback, get_feedback_stats, get_all_corrections
import requests

app = Flask(__name__, template_folder='../web/templates')

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    data = request.get_json(silent=True) or {}
    question = data.get('message', '').strip()
    
    if not question:
        return jsonify({'error': 'Mesaj boş'}), 400
    
    print(f"\n{'='*60}")
    print(f"SORU: {question}")
    print('='*60)
    
    # Selamlaşma kontrolü
    greetings = ['merhaba', 'selam', 'hey', 'hi', 'hello', 'günaydın', 'iyi günler']
    if any(g in question.lower() for g in greetings) and len(question.split()) <= 3:
        return jsonify({
            'success': True,
            'message': 'Merhaba! Size satınalma, sipariş, firma ve proje bilgileri hakkında yardımcı olabilirim.',
            'sql': None,
            'raw_results': []
        })
    
    # 1. SQL üret
    sql = generate_sql(question)
    print(f"SQL: {sql}")
    
    if not sql:
        return jsonify({
            'success': False,
            'message': 'Sorunuz için uygun bir sorgu oluşturulamadı. Lütfen daha açık bir şekilde sorun.',
            'sql': None
        })
    
    # 2. Güvenlik kontrolü
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return jsonify({
            'success': False,
            'message': error,
            'sql': sql
        })
    
    # 3. Sorguyu çalıştır
    results, columns, error = run_query(sql)
    
    if error:
        print(f"SQL HATA: {error}")
        return jsonify({
            'success': False,
            'message': f'Sorgu hatası: {error}',
            'sql': sql
        })
    
    print(f"SONUÇ: {len(results) if results else 0} kayıt")
    
    # 4. Sonuçları açıkla
    explanation = explain_results(question, results)
    
    return jsonify({
        'success': True,
        'message': explanation,
        'sql': sql,
        'raw_results': results[:100] if results else [],
        'total_count': len(results) if results else 0
    })

def explain_results(question, results):
    """Sonuçları Türkçe açıkla"""
    if not results:
        return "Sonuç bulunamadı."
    
    # Basit sonuçlar için hızlı cevap
    if len(results) == 1 and len(results[0]) <= 3:
        parts = []
        for key, value in results[0].items():
            if isinstance(value, (int, float)):
                formatted = f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                parts.append(f"**{key}**: {formatted}")
            else:
                parts.append(f"**{key}**: {value}")
        return " | ".join(parts)
    
    # Özet bilgi
    return f"{len(results)} kayıt bulundu."

@app.route('/api/test-db')
def test_db():
    """Veritabanı bağlantı testi"""
    from sql_ai.run_sql import get_connection
    conn = get_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'})

@app.route('/api/test-ollama')
def test_ollama():
    """Ollama bağlantı testi"""
    try:
        response = requests.get(f"{LLM_CONFIG['base_url']}/api/tags", timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'ok'})
    except:
        pass
    return jsonify({'status': 'error'})

@app.route('/api/health')
def health():
    """Sistem sağlık kontrolü"""
    from sql_ai.run_sql import get_connection
    
    status = {
        'database': False,
        'ollama': False,
        'rag': False
    }
    
    # DB
    conn = get_connection()
    if conn:
        conn.close()
        status['database'] = True
    
    # Ollama
    try:
        response = requests.get(f"{LLM_CONFIG['base_url']}/api/tags", timeout=5)
        if response.status_code == 200:
            status['ollama'] = True
    except:
        pass
    
    # RAG
    if os.path.exists('data/vector_db/embeddings.npy'):
        status['rag'] = True
    
    return jsonify(status)


@app.route('/api/correct', methods=['POST'])
def correct_query():
    """
    Kullanıcı düzeltmesi al ve öğren
    Body: {question, wrong_sql, correct_sql}
    """
    data = request.get_json(silent=True) or {}
    question = data.get('question', '')
    wrong_sql = data.get('wrong_sql', '')
    correct_sql = data.get('correct_sql', '')
    
    if not all([question, wrong_sql, correct_sql]):
        return jsonify({'error': 'question, wrong_sql ve correct_sql gerekli'}), 400
    
    # Düzeltmeyi kaydet ve öğren
    learn_from_correction(question, wrong_sql, correct_sql)
    
    return jsonify({
        'success': True,
        'message': 'Düzeltme kaydedildi ve öğrenildi!'
    })


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Kullanıcı geri bildirimi
    Body: {question, sql, is_correct, comment}
    """
    data = request.get_json(silent=True) or {}
    question = data.get('question', '')
    sql = data.get('sql', '')
    is_correct = data.get('is_correct', False)
    comment = data.get('comment', '')
    
    save_feedback(question, sql, is_correct, comment)
    
    # Eğer doğruysa, başarılı örnek olarak kaydet
    if is_correct and sql:
        from learning.feedback_system import add_learned_example
        add_learned_example(question, sql)
    
    return jsonify({'success': True})


@app.route('/api/stats')
def get_stats():
    """İstatistikleri getir"""
    stats = get_feedback_stats()
    corrections = get_all_corrections()
    
    return jsonify({
        'feedback': stats,
        'corrections_count': len(corrections)
    })


@app.route('/api/corrections')
def list_corrections():
    """Tüm düzeltmeleri listele"""
    corrections = get_all_corrections()
    return jsonify(corrections)


if __name__ == '__main__':
    print("="*60)
    print("   ERP AI RAG - Akıllı Veritabanı Asistanı")
    print("="*60)
    print("\n🌐 http://localhost:5000")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
