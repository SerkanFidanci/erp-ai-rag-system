# ERP AI RAG System

ERP AI RAG System, ERP veritabanı üzerinde **Türkçe doğal dil ile güvenli SQL sorgulama** sağlayan bir backend projesidir. Kullanıcının sorusunu LLM + RAG yaklaşımı ile SQL'e çevirir, güvenlik filtresinden geçirir ve sonucu API üzerinden döner.

## Projenin Amacı
- ERP veritabanlarında teknik olmayan ekiplerin doğal dil ile soru sorabilmesini sağlamak
- LLM tabanlı SQL üretimini şema bilgisiyle (RAG) desteklemek
- Sorgu güvenliğini `SELECT`-only yaklaşımıyla korumak
- Kullanıcı düzeltmelerini saklayıp zamanla daha iyi sonuç üretmek

## Öne Çıkan Özellikler
- **NL → SQL üretimi** (`sql_ai/nl_to_sql.py`)
- **RAG tabanlı bağlam zenginleştirme** (`rag/query_rag.py`, `rag/build_vector_db.py`)
- **SQL güvenlik doğrulaması** (`sql_ai/sql_validator.py`)
- **Geri bildirim / düzeltme öğrenme döngüsü** (`learning/feedback_system.py`)
- **Flask REST API + web arayüzü** (`api/app.py`, `web/templates/index.html`)

---

## Mimari Akış
1. Kullanıcı sorusu `/api/chat` endpoint’ine gelir.
2. Sistem, soruya göre ilgili tablo/ilişki bilgisini RAG ile toplar.
3. LLM prompt’una şema + sorgu kalıpları + öğrenilmiş örnekler eklenir.
4. Üretilen SQL sorgusu güvenlik katmanından geçer.
5. SQL Server’da sorgu çalıştırılır ve sonuçlar JSON olarak döner.

---

## Klasör Yapısı
- `api/` → Flask endpoint’leri
- `config/` → DB / LLM / RAG / güvenlik ayarları
- `sql_ai/` → SQL üretimi, çalışma ve doğrulama
- `rag/` → embedding, vector DB oluşturma ve arama
- `schema/` → şema çıkarma ve temizleme araçları
- `learning/` → feedback, düzeltme, öğrenilmiş örnek kayıtları
- `finetuning/` → fine-tuning yardımcı dosyaları
- `web/` → HTML arayüz

---

## Gereksinimler
- Python 3.10+
- SQL Server erişimi
- ODBC Driver 17 for SQL Server
- Ollama (lokal model servis)

Python bağımlılıkları:
```bash
pip install -r requirements.txt
```

---

## Konfigürasyon (Önemli)
Proje artık environment variable destekler.

1) Örnek dosyayı kopyalayın:
```bash
cp .env.example .env
```

2) Değerleri kendi ortamınıza göre düzenleyin (`ERP_DB_*`, `ERP_LLM_*` vb.).

3) Uygulamayı başlatmadan önce ortam değişkenlerini yükleyin:
```bash
set -a && source .env && set +a
```

> Not: Uygulama `config/db_config.py` içinde env değişkenlerini okur. Env yüklenmezse dosyadaki default değerleri kullanır.

### Kritik Değişkenler
- `ERP_DB_SERVER`, `ERP_DB_NAME`, `ERP_DB_USER`, `ERP_DB_PASSWORD`
- `ERP_LLM_BASE_URL`, `ERP_LLM_MODEL`
- `ERP_RAG_VECTOR_DB_PATH`

---

## Kurulum ve Çalıştırma
### 1) İlk kurulum (schema + RAG index)
```bash
python main.py setup
```

### 2) Sistem kontrolü
```bash
python main.py check
```

### 3) Sunucuyu başlat
```bash
python main.py run
```

Uygulama varsayılan olarak:
- Web: `http://localhost:5000`
- API: `http://localhost:5000/api/...`

---

## API Endpoint Özeti
- `POST /api/chat` → Soru sor, SQL üret ve çalıştır
- `POST /api/correct` → Hatalı SQL için doğru SQL düzeltmesi gönder
- `POST /api/feedback` → Sonuç doğru/yanlış geri bildirimi
- `GET /api/health` → DB / Ollama / RAG sağlık durumu
- `GET /api/stats` → Feedback ve düzeltme istatistikleri
- `GET /api/corrections` → Kaydedilen düzeltmeleri listele

### Örnek `POST /api/chat`
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Bu ay kaç satınalma siparişi var?"}'
```

---

## CV / Portfolyo İçin Kullanım
Bu projeyi CV’de şu şekilde konumlandırabilirsiniz:
- **Applied AI / Backend**: ERP veritabanı için Türkçe doğal dil sorgulama sistemi
- **RAG + LLM Engineering**: şema tabanlı prompt zenginleştirme ve SQL üretim pipeline’ı
- **AI Safety / Data Security**: SQL doğrulama ve zararlı komut engelleme

Örnek kısa cümle:
> “ERP veritabanları için Türkçe doğal dil sorgularını RAG destekli ve güvenli SQL’e dönüştüren bir AI backend sistemi geliştirdim; kullanıcı düzeltmelerinden öğrenen feedback döngüsü kurdum.”

---

## Production’a Geçmeden Önce
- `debug=False` ile çalıştırın
- Secret ve bağlantı bilgilerini env/secrets manager üzerinden yönetin
- API authentication / rate limiting ekleyin
- Loglama ve izleme (monitoring) entegre edin
- `data/` içindeki öğrenme dosyaları için yedekleme stratejisi belirleyin

---

## Bilinen Ortam Sorunları ve Çözüm İpuçları
- **`ODBC Driver 17 for SQL Server` bulunamadı** → driver kurulumu eksik
- **Ollama erişilemiyor** → `ollama serve` çalıştırın
- **Model yok** → `ollama pull qwen2.5-coder:7b`
- **RAG dosyaları yok** → `python main.py setup` çalıştırın
