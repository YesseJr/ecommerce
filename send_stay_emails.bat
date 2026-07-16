@echo off
REM ============================================================
REM Daily stay-email runner for BookMyStay (Windows Task Scheduler)
REM
REM Edit PROJECT_DIR below to match where manage.py actually lives
REM on this machine, then point Task Scheduler at THIS FILE (not
REM at python.exe directly) — see instructions in the chat.
REM ============================================================

set PROJECT_DIR=C:\path\to\your\ecommerce
set VENV_PYTHON=%PROJECT_DIR%\venv\Scripts\python.exe

cd /d "%PROJECT_DIR%"

echo [%date% %time%] Running send_stay_emails >> "%PROJECT_DIR%\stay_emails_log.txt"
"%VENV_PYTHON%" manage.py send_stay_emails >> "%PROJECT_DIR%\stay_emails_log.txt" 2>&1
echo [%date% %time%] Done >> "%PROJECT_DIR%\stay_emails_log.txt"
echo. >> "%PROJECT_DIR%\stay_emails_log.txt"
