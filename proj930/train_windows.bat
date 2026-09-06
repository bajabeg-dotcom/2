@echo off
setlocal EnableExtensions
chcp 65001 >nul
title DNA MIDI Studio Pa800 - Neural Training
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
    echo BLOCKED: Python 3 nije instaliran ili nije na PATH-u.
    set "RC=1"
    goto finish
)

echo ============================================================
echo DNA MIDI Studio - Neural Training launcher
echo ============================================================
echo Python:
%PY% --version
if errorlevel 1 (
    echo BLOCKED: Python interpreter nije pokrenut.
    set "RC=1"
    goto finish
)

echo.
echo Provjera zavisnosti za neuralni trening...
%PY% -m pip show torch >nul 2>nul
if errorlevel 1 (
    echo Instalacija PyTorch CPU paketa...
    %PY% -m pip install torch --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 (
        echo BLOCKED: PyTorch instalacija nije uspjela.
        set "RC=1"
        goto finish
    )
)
%PY% -m pip show numpy >nul 2>nul
if errorlevel 1 (
    echo Instalacija NumPy...
    %PY% -m pip install numpy
    if errorlevel 1 (
        echo BLOCKED: NumPy instalacija nije uspjela.
        set "RC=1"
        goto finish
    )
)
%PY% -m pip show mido >nul 2>nul
if errorlevel 1 (
    echo Instalacija mido za runtime provjeru...
    %PY% -m pip install mido
    if errorlevel 1 (
        echo BLOCKED: mido instalacija nije uspjela.
        set "RC=1"
        goto finish
    )
)

echo.
echo 1. Canonical neural training/calibration launcher
echo 2. Izgradi katalog instrumenata
echo 3. Prosiri Factory velocity profile
echo.
set "CHOICE="
set /p "CHOICE=Izbor: "
if "%CHOICE%"=="1" goto neural_launcher
if "%CHOICE%"=="2" goto instrument_catalog
if "%CHOICE%"=="3" goto factory_velocity

echo Neispravan izbor.
set "RC=1"
goto finish

:neural_launcher
call "%~dp0TRAIN_NEURAL_NETWORK.bat"
set "RC=%ERRORLEVEL%"
goto finish

:instrument_catalog
if not exist "scripts\build_instrument_catalog.py" (
    echo BLOCKED: scripts\build_instrument_catalog.py nije pronadjen.
    set "RC=2"
    goto finish
)
%PY% "scripts\build_instrument_catalog.py"
set "RC=%ERRORLEVEL%"
goto utility_result

:factory_velocity
if not exist "scripts\expand_factory_velocity.py" (
    echo BLOCKED: scripts\expand_factory_velocity.py nije pronadjen.
    set "RC=2"
    goto finish
)
%PY% "scripts\expand_factory_velocity.py"
set "RC=%ERRORLEVEL%"

:utility_result
if "%RC%"=="0" (
    echo Utility command completed. Neural/model certification was not changed.
) else (
    echo Utility command FAILED or was BLOCKED.
)

goto finish

:finish
echo.
if "%RC%"=="0" (
    echo Launcher zavrsen bez greske. Neural status ostaje evidence-gated.
) else (
    echo Launcher je BLOCKED/FAILED. Nema tihog promotiona niti PASS tvrdnje.
)
pause
exit /b %RC%
