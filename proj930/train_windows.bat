@echo off
chcp 65001 >nul
title DNA MIDI Studio Pa800 — Neural Training

echo ============================================================
echo  DNA MIDI Studio Pa800 v9.30 — Lokalni Trening
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python nije instaliran!
    echo  Skini Python 3.10+ sa https://www.python.org/downloads/
    echo  VAŽNO: Checkbox "Add Python to PATH"
    pause
    exit /b 1
)

:: Install dependencies if needed
echo Provjera zavisnosti...
pip show torch >nul 2>&1
if errorlevel 1 (
    echo  Instalacija PyTorch CPU...
    pip install torch --index-url https://download.pytorch.org/whl/cpu
)
pip show numpy >nul 2>&1
if errorlevel 1 (
    echo  Instalacija NumPy...
    pip install numpy
)
pip show mido >nul 2>&1
if errorlevel 1 (
    echo  Instalacija mido...
    pip install mido
)

echo.
echo ✅ Sve zavisnosti spremne
echo.

echo Šta želiš trenirati?
echo   1) Core DNA Reconstructor (8 epoha)
echo   2) Relationship Sequence Transformer (12 epoha)
echo   3) Oba modela + kalibracija
echo   4) Samo kalibracioni gate
echo   5) Izgradi katalog instrumenata
echo   6) Proširi Factory velocity profile
echo.
set /p choice="Tvoj izbor (1-6): "

if "%choice%"=="1" (
    echo.
    echo 🧠 Treniranje Core modela (8 epoha)...
    python scripts/train_local.py --mode core --epochs 8
)
if "%choice%"=="2" (
    echo.
    echo 🧠 Treniranje Relationship modela (12 epoha)...
    python scripts/train_local.py --mode relationship --epochs 12
)
if "%choice%"=="3" (
    echo.
    echo 🧠 Treniranje oba modela + kalibracija...
    python scripts/train_local.py --mode all --promote
)
if "%choice%"=="4" (
    echo.
    echo 🔍 Kalibracioni gate...
    python scripts/train_local.py --mode calibrate
)
if "%choice%"=="5" (
    echo.
    echo 📋 Izgradnja kataloga instrumenata...
    python scripts/build_instrument_catalog.py
)
if "%choice%"=="6" (
    echo.
    echo 🎹 Proširenje Factory velocity profila...
    python scripts/expand_factory_velocity.py
)

echo.
echo ============================================================
echo  Završeno!
echo ============================================================
pause
