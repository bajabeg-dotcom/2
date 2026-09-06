@echo off
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"

where py >nul 2>nul
if not errorlevel 1 set "DNA_PYTHON=py -3"
if not defined DNA_PYTHON where python >nul 2>nul
if not defined DNA_PYTHON if not errorlevel 1 set "DNA_PYTHON=python"
if not defined DNA_PYTHON (
  echo ERROR: Python 3.11-3.14 was not found.
  pause
  exit /b 1
)

%DNA_PYTHON% package_selfcheck.py
if errorlevel 1 goto failed
%DNA_PYTHON% release_check.py
if errorlevel 1 goto failed
%DNA_PYTHON% recovery_release_check.py
if errorlevel 1 goto failed

echo Complete DNA MIDI Studio release check: PASS
pause
exit /b 0

:failed
echo DNA MIDI Studio release check: FAILED
pause
exit /b 1
