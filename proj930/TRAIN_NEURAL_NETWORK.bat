@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
set "PYTHONUTF8=1"
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo ERROR: Python 3 nije pronadjen.
  pause & exit /b 1
)

echo ======================================================
echo DNA MIDI STUDIO 9.02 - NEURAL TRAINING
echo ======================================================
echo 1. Brzi test treninga ^(bez promotiona^)
echo 2. Treniraj CORE mrezu
echo 3. Treniraj TERCA/ECHO relationship mrezu
echo 4. Treniraj obje mreze
echo 5. Kalibracija/validacija postojecih modela
echo 6. Treniraj obje i PROMOVISI nakon PASS gatea
echo.
set /p CHOICE=Izbor: 
if "%CHOICE%"=="1" %PY% scripts\train_neural_network.py --mode all --epochs 2 --relationship-epochs 2 --max-train-samples 512 --max-validation-samples 128 --max-holdout-samples 128
if "%CHOICE%"=="2" %PY% scripts\train_neural_network.py --mode core
if "%CHOICE%"=="3" %PY% scripts\train_neural_network.py --mode relationship
if "%CHOICE%"=="4" %PY% scripts\train_neural_network.py --mode all
if "%CHOICE%"=="5" %PY% scripts\train_neural_network.py --mode calibrate
if "%CHOICE%"=="6" %PY% scripts\train_neural_network.py --mode all --promote
if errorlevel 1 goto fail
echo.
echo PASS. Izvjestaj: artifacts\neural_training_run_9.02.json
pause & exit /b 0
:fail
echo.
echo FAILED - stari production modeli nisu obrisani.
pause & exit /b 1
