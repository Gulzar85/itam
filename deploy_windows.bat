@echo of
echo ==========================================
echo  ITAM - Windows Server Deployment
echo ==========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and configure it.
    exit /b 1
)

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput --settings=config.settings.production

REM Run migrations
echo Running migrations...
python manage.py migrate --settings=config.settings.production

REM Create superuser (optional)
REM python manage.py createsuperuser --settings=config.settings.production

echo.
echo ==========================================
echo  Deployment ready!
echo ==========================================
echo.
echo To run the server:
echo   python manage.py runserver 0.0.0:8000 --settings=config.settings.production
echo.
echo Or with Waitress (recommended for production):
echo   pip install waitress
echo   waitress-serve --port=8000 config.wsgi:application
echo.
pause