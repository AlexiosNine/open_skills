@echo off
REM Start script for OpenSkill Skill Host (Windows)

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Error: Virtual environment not found. Please run setup.bat first
    exit /b 1
)

REM Activate virtual environment
call ..\.venv\Scripts\activate.bat

REM Get host and port from environment or use defaults
if "%OPENSKILL_HOST%"=="" set OPENSKILL_HOST=127.0.0.1
if "%OPENSKILL_PORT%"=="" set OPENSKILL_PORT=8000

echo 🚀 Starting OpenSkill Skill Host...
echo 📍 Server will be available at http://%OPENSKILL_HOST%:%OPENSKILL_PORT%
echo.

REM Start the server
uvicorn src.app:app --host %OPENSKILL_HOST% --port %OPENSKILL_PORT% --reload

