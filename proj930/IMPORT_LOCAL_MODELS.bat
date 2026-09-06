@echo off
setlocal
cd /d "%~dp0"
if not exist "models\midigpt" mkdir "models\midigpt"
for %%F in (yellow_small-final.zip yellow_medium-final.zip) do (
  if exist "%%F" (
    echo Extracting %%F...
    powershell -NoProfile -Command "Expand-Archive -LiteralPath '%CD%\%%F' -DestinationPath '%CD%\models\midigpt' -Force"
  ) else (
    echo Missing %%F next to this project folder.
  )
)
echo.
echo Expected hashes:
type "models\midigpt\SHA256SUMS.txt"
echo.
echo Done. MIDI-GPT worker will prefer local checkpoints automatically.
pause
