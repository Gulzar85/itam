# ITAM - IT Asset Management System
## Windows Server Deployment

### Prerequisites
- Python 3.8+ installed
- Windows Server 2016/2019/2022

### Quick Setup

1. **Clone/Extract project**
   ```
   cd C:\inetpub\wwwroot\ITAM
   ```

2. **Create `.env` file**
   ```
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=localhost,your-server-ip
   ```

3. **Run deployment script**
   ```
   deploy_windows.bat
   ```

4. **Start the server**
   ```
   # Development server (testing)
   python manage.py runserver 0.0.0.0:8000 --settings=config.settings.production
   
   # Production with Waitress (recommended)
   pip install waitress
   waitress-serve --port=8000 config.wsgi:application
   ```

### Using IIS (Optional)

1. Install IIS with CGI support
2. Install `wfastcgi`:
   ```
   pip install wfastcgi
   ```
3. Configure IIS to use `wfastcgi` with `config.wsgi:application`

### Settings

- **Development**: `config.settings.development`
- **Production**: `config.settings.production`
- **Override**: Set `DJANGO_SETTINGS_MODULE` or `ENV_NAME` environment variable

### Database

Uses **SQLite** by default (no PostgreSQL required for Windows Server).

### Static Files

Collect static files for production:
```
python manage.py collectstatic --settings=config.settings.production
```

Static files will be in `staticfiles/` directory.

---

## Environment Variables (.env)

| Variable | Default | Description |
|-----------|---------|-------------|
| SECRET_KEY | (required) | Django secret key |
| DEBUG | False | Debug mode |
| ALLOWED_HOSTS | localhost,127.0.0.1 | Comma-separated hosts |
| DJANGO_SETTINGS_MODULE | config.settings.production | Override settings |
