@echo off
cd /d "%~dp0"

if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install -r requirement.txt

python main.py

pause