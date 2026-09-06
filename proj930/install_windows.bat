@echo off
setlocal EnableExtensions
chcp 65001 >nul
title DNA MIDI Studio Pa800 - Install neural dependencies
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PY="

where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo BLOCKED: Python 3 nije pronadjen.
    set "RC=1"
    goto finish
)

%PY% --version
if errorlevel 1 goto failed
echo.
echo Instalacija/verifikacija PyTorch CPU, NumPy i mido...
%PY% -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto failed
%PY% -m pip install numpy mido
if errorlevel 1 goto failed

%PY% -c "import torch, numpy, mido; print('torch', torch.__version__); print('numpy', numpy.__version__); print('mido', getattr(mido, '__version__', 'installed'))"
if errorlevel 1 goto failed

echo.
echo Zavisnosti su instalirane.
if not exist "src\dna_midi_studio\ai_learning\trainer.py" (
    echo BLOCKED: neural learning runtime nedostaje u src\dna_midi_studio.
    echo Instalacija paketa sama ne stvara nedostajuci source kod.
    set "RC=2"
    goto finish
)

echo Neural learning runtime je pronadjen.
set "RC=0"
goto finish

:failed
echo BLOCKED: instalacija ili import dependency paketa nije uspio.
set "RC=1"

:finish
echo.
if "%RC%"=="0" (
    echo Install check: OK. Kalibraciju pokreni kroz TRAIN_NEURAL_NETWORK.bat.
) else (
    echo Install check: BLOCKED/FAILED. Neuralni modeli nisu promovirani.
)
pause
exit /b %RC%
