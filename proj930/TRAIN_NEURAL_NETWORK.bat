@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PY="
set "REPORT_READY=0"

where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo ERROR: Python 3 nije pronadjen.
  set "RC=1"
  goto finish
)

if not exist "scripts\train_local.py" (
  echo ERROR: scripts\train_local.py nije pronadjen.
  set "RC=1"
  goto finish
)
if not exist "learning_data\dataset_manifest.json" (
  echo ERROR: learning_data\dataset_manifest.json nije pronadjen.
  set "RC=1"
  goto finish
)
if not exist "relationship_sequence_data_v2\relationship_sequence_manifest_v2.json" (
  echo ERROR: relationship sequence manifest nije pronadjen.
  set "RC=1"
  goto finish
)

echo ======================================================
echo DNA MIDI STUDIO - CANONICAL NEURAL TRAINING
echo ======================================================
echo 1. FULL trening obje mreze ^(bez promotiona^)
echo 2. Treniraj CORE mrezu
echo 3. Treniraj RELATIONSHIP mrezu
echo 4. Provjeri kalibraciju stvarnih modela
echo 5. FULL trening obje mreze + PROMOCIJA kroz learning gate
echo.
set "CHOICE="
set /p "CHOICE=Izbor: "

if "%CHOICE%"=="4" goto run_calibration
if "%CHOICE%"=="1" goto require_runtime
if "%CHOICE%"=="2" goto require_runtime
if "%CHOICE%"=="3" goto require_runtime
if "%CHOICE%"=="5" goto require_runtime

echo Neispravan izbor.
set "RC=1"
goto finish

:require_runtime
if not exist "src\dna_midi_studio\ai_learning\trainer.py" (
  echo BLOCKED: src\dna_midi_studio\ai_learning\trainer.py nedostaje.
  echo Trening nije pokrenut i nijedan model nije promovisan.
  set "RC=2"
  goto finish
)
if not exist "src\dna_midi_studio\ai_learning\relationship_sequence_trainer.py" (
  echo BLOCKED: relationship_sequence_trainer.py nedostaje.
  echo Trening nije pokrenut i nijedan model nije promovisan.
  set "RC=2"
  goto finish
)

set "REPORT_READY=1"
if "%CHOICE%"=="1" %PY% "scripts\train_local.py" --mode all
if "%CHOICE%"=="2" %PY% "scripts\train_local.py" --mode core
if "%CHOICE%"=="3" %PY% "scripts\train_local.py" --mode relationship
if "%CHOICE%"=="5" %PY% "scripts\train_local.py" --mode all --promote
set "RC=%ERRORLEVEL%"
goto report_result

:run_calibration
set "REPORT_READY=1"
%PY% "scripts\train_local.py" --mode calibrate
set "RC=%ERRORLEVEL%"

:report_result
if "%CHOICE%"=="4" (
  if "%RC%"=="0" (
    echo Neural artifact check completed. Check status in artifacts\neural_training_run_9.30.json.
  ) else (
    echo Neural calibration is BLOCKED or incomplete. No PASS claim was emitted.
  )
) else (
  if "%RC%"=="0" (
    echo Training command completed. Promotion/export status remains evidence-gated.
  ) else (
    echo Training command FAILED or was BLOCKED. No model was silently promoted.
  )
)

goto finish

:finish
echo.
if "%REPORT_READY%"=="1" (
  echo Report: artifacts\neural_training_run_9.30.json
) else (
  echo No new neural report was written.
)
pause
exit /b %RC%
