@echo off
echo =========================================
echo  ITAM - Windows Server Deployment (FastCGI)
echo =========================================
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

REM Enable FastCGI
echo Enabling FastCGI...
wfastcgi-enable 2>nul || echo FastCGI already enabled or running as admin required

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput --settings=config.settings.production

REM Run migrations
echo Running migrations...
python manage.py migrate --settings=config.settings.production

REM Create superuser (optional)
REM python manage.py createsuperuser --settings=config.settings.production

echo.
echo =========================================
echo  Deployment ready for FastCGI!
echo =========================================
echo.
echo Next steps for IIS + FastCGI:
echo 1. Install IIS with CGI feature enabled
echo 2. Copy web.config to your IIS site root
echo 3. Update web.config with correct Python path:
echo    ScriptProcessor="C:\path\to\.venv\Scripts\python.exe|C:\path\to\.venv\Lib\site-packages\wfastcgi.py"
echo 4. Grant IIS permissions to project folder
echo 5. Browse to your site
echo.
echo For testing without IIS:
echo   python manage.py runserver 0.0.0.0:8000 --settings=config.settings.production
echo.
pause