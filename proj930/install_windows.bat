@echo off
chcp 65001 >nul
title DNA MIDI Studio Pa800 — Instalacija

echo ============================================================
echo  DNA MIDI Studio Pa800 v9.30 — Instalacija
echo  Za Korg Pa800 (OS 2.0+)
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python nije instaliran!
    echo  Skini Python 3.10+ sa https://www.python.org/downloads/
    echo  VAŽNO: Checkbox "Add Python to PATH" pri instalaciji
    echo.
    echo  Nakon instalacije Pythona, ponovo pokreni ovu skriptu.
    pause
    exit /b 1
)

echo ✅ Python pronadjen:
python --version

echo.
echo Instalacija zavisnosti...
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install numpy mido

echo.
echo ============================================================
echo  ✅ Instalacija zavrsena!
echo ============================================================
echo.
echo  Za pocetak:
echo    1. Pokreni: train_windows.bat
echo    2. Izaberi opciju za trening
echo    3. Ili pokreni GUI: python server.py
eco.

:: Quick test
echo.
echo Brzi test modula...
python -c "import torch; import numpy; import mido; print('  ✅ torch', torch.__version__); print('  ✅ numpy', numpy.__version__); print('  ✅ mido', mido.__version__)

echo.
pause
