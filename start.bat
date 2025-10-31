@echo off
echo ======================================
echo Organization Management System
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Run migrations
echo Setting up database...
python manage.py makemigrations
python manage.py migrate

REM Ask about superuser
echo.
echo ======================================
echo Do you want to create an admin user?
echo ======================================
set /p create_user="(y/n): "

if /i "%create_user%"=="y" (
    python manage.py createsuperuser
)

REM Start server
echo.
echo ======================================
echo Starting Organization Management System...
echo ======================================
echo Access the application at: http://localhost:8000/
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver

pause
