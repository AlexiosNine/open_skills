@echo off
REM Setup script for OpenSkill Skill Host (Windows)

echo 🚀 Setting up OpenSkill Skill Host environment...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: python is not installed
    exit /b 1
)

echo 📌 Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python 3.10+ is required
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Setup completed successfully!
echo.
echo To activate the virtual environment, run:
echo   .venv\Scripts\activate
echo.
echo To start the Skill Host, run:
echo   scripts\start.bat
echo.

