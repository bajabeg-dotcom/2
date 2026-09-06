@echo off
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"

where py >nul 2>nul
if not errorlevel 1 goto use_py
where python >nul 2>nul
if not errorlevel 1 goto use_python

echo ERROR: Python 3.11-3.14 was not found.
echo Install Python and enable "Add Python to PATH".
pause
exit /b 1

:use_py
py -3 server.py
exit /b %errorlevel%

:use_python
python server.py
exit /b %errorlevel%
