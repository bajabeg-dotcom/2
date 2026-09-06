@echo off
setlocal
cd /d "%~dp0.."
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install numpy symusic tqdm tokenizers huggingface_hub
python -m pip install -e third_party\miditok
python -c "from miditok import REMI,TokenizerConfig; t=REMI(TokenizerConfig(use_programs=True,one_token_stream_for_programs=True,use_time_signatures=True,use_velocities=False)); print('MidiTok REMI+ OK')"
endlocal
