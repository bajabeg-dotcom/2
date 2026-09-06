@echo off
setlocal
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
cd /d "%~dp0"
set "PYTHONUTF8=1"

if not exist "prism-uploads\DNA.zip" (
  echo ERROR: Authoritative archive prism-uploads\DNA.zip is missing.
  pause
  exit /b 1
)

where py >nul 2>nul
if not errorlevel 1 set "DNA_PYTHON=py -3"
if not defined DNA_PYTHON where python >nul 2>nul
if not defined DNA_PYTHON if not errorlevel 1 set "DNA_PYTHON=python"
if not defined DNA_PYTHON (
  echo ERROR: Python 3.11-3.14 was not found.
  pause
  exit /b 1
)

%DNA_PYTHON% dna_builder.py "prism-uploads\DNA.zip" --output data
if errorlevel 1 goto failed
%DNA_PYTHON% release_check.py
if errorlevel 1 goto failed

echo DNA registry rebuild and legacy release check: PASS
pause
exit /b 0

:failed
echo DNA registry rebuild or release check: FAILED
pause
exit /b 1
