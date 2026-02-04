@echo off
echo ========================================
echo  Honeypot Scam Detection API
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Creating from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file and add your API keys!
    echo Press any key to open .env in notepad...
    pause >nul
    notepad .env
    echo.
    echo After saving .env, press any key to start server...
    pause >nul
)

REM Check if waitress is installed
pip show waitress >nul 2>&1
if errorlevel 1 (
    echo Installing waitress server...
    pip install waitress
    echo.
)

echo.
echo ========================================
echo  Starting Honeypot API Server
echo ========================================
echo  URL: http://localhost:5000
echo  Health: http://localhost:5000/health
echo.
echo  Press CTRL+C to stop the server
echo ========================================
echo.

REM Start the server
python app.py

REM If python app.py fails, try waitress
if errorlevel 1 (
    echo.
    echo Flask development server failed, trying waitress...
    waitress-serve --host=0.0.0.0 --port=5000 app:app
)

pause
