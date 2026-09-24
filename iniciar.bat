@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Criando ambiente Python...
  python -m venv .venv || (echo Instale o Python 3.10+ em https://www.python.org/downloads/ & pause & exit /b 1)
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\python app.py
pause
