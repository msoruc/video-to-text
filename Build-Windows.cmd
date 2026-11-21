@echo off
setlocal
cd /d "%~dp0"
if not exist "assets\ggml-base.bin" (
  echo Copy the assets folder containing ggml-base.bin beside this script.
  exit /b 1
)
py -3.12-64 -m venv .venv-win || exit /b 1
set "PY=.venv-win\Scripts\python.exe"
"%PY%" -c "import platform, tkinter; assert platform.machine().upper() in ('AMD64','X86_64'), 'Use x64 Python 3.12'" || exit /b 1
"%PY%" -c "import hashlib,pathlib; p=pathlib.Path('assets/ggml-base.bin'); assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe','Invalid model file'" || exit /b 1
"%PY%" -m pip install --only-binary=:all: -r requirements.txt || exit /b 1
"%PY%" -m PyInstaller --noconfirm --distpath dist-windows --workpath build-windows VideoToText.spec || exit /b 1
echo Ready: dist-windows\Video to Text\Video to Text.exe
