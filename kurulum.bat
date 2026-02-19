@echo off
chcp 65001 >nul
title ERP AI RAG - Kurulum

echo ============================================
echo    ERP AI RAG - Akıllı Veritabanı Asistanı
echo ============================================
echo.

:: Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadı!
    echo Python'u https://python.org adresinden indirin.
    pause
    exit /b 1
)
echo [OK] Python bulundu

:: Paketleri kur
echo.
echo [*] Python paketleri kuruluyor...
pip install -r requirements.txt

if errorlevel 1 (
    echo [HATA] Paket kurulumu başarısız!
    pause
    exit /b 1
)
echo [OK] Paketler kuruldu

:: Ollama kontrolü
echo.
echo [*] Ollama kontrol ediliyor...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [UYARI] Ollama bulunamadı!
    echo Ollama'yı https://ollama.com/download adresinden indirin.
    echo.
) else (
    echo [OK] Ollama bulundu
)

echo.
echo ============================================
echo    YAPILANDIRMA
echo ============================================
echo.
echo 1. config/db_config.py dosyasını düzenleyin
echo    - server: Veritabanı sunucu adresi
echo    - database: Veritabanı adı
echo    - username: Kullanıcı adı
echo    - password: Şifre
echo.
echo 2. Ollama'yı başlatın (ayrı CMD'de):
echo    ollama serve
echo.
echo 3. Model kurun:
echo    ollama pull qwen2.5-coder:7b
echo.
echo ============================================
echo.

set /p setup="RAG sistemini kurmak ister misiniz? (E/H): "
if /i "%setup%"=="E" (
    echo.
    echo [*] RAG sistemi kuruluyor...
    python main.py setup
)

echo.
set /p start="Sunucuyu başlatmak ister misiniz? (E/H): "
if /i "%start%"=="E" (
    echo.
    echo [*] Sunucu başlatılıyor...
    echo [*] Tarayıcıda aç: http://localhost:5000
    python main.py run
)

pause
