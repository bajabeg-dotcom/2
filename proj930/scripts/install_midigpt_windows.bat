@echo off
setlocal
cd /d "%~dp0.."
echo ======================================================
echo DNA MIDI Studio - VENDORED MIDI-GPT 0.3.4 installer
echo ======================================================
where py >nul 2>nul || (echo Python launcher 'py' not found.& exit /b 1)
if not exist .venv-midigpt (
  py -3.11 -m venv .venv-midigpt || py -3.10 -m venv .venv-midigpt || py -3.12 -m venv .venv-midigpt || (echo Python 3.10-3.12 required.& exit /b 1)
)
call .venv-midigpt\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
REM Install the exact reviewed source shipped with DNA MIDI Studio.
python -m pip install -e "third_party\MIDI-GPT-0.3.4[inference]"
if errorlevel 1 exit /b 1
python scripts\midigpt_worker.py --self-test
if errorlevel 1 exit /b 1
echo.
echo MIDI-GPT 0.3.4 backend installed from bundled MIT-licensed source.
echo Pretrained checkpoint is downloaded from Metacreation/MIDI-GPT on first generation.
endlocal
