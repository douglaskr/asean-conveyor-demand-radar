@echo off
REM Weekly automation launcher for Windows Task Scheduler
SETLOCAL

cd /d %~dp0
if not exist .venv (
  echo [ERROR] .venv not found. Create virtual environment first.
  exit /b 1
)

call .venv\Scripts\activate.bat
python -m src.main >> logs\weekly_run.log 2>&1

ENDLOCAL
