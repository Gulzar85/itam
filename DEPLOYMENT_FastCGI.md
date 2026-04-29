# ITAM - FastCGI Deployment on Windows Server (IIS)

## Prerequisites

- Windows Server 2016/2019/2022 with IIS installed
- IIS CGI feature enabled
- Python 3.8+ installed
- Project files deployed to `C:\inetpub\wwwroot\ITAM` (or your preferred location)

---

## Step 1: Install wfastcgi

```bash
pip install wfastcgi
wfastcgi-enable
```

This registers FastCGI with IIS.

---

## Step 2: Configure web.config

Update `web.config` with your Python path:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI"
           path="*"
           verb="*"
           modules="FastCgiModule"
           scriptProcessor="C:\path\to\your\.venv\Scripts\python.exe|C:\path\to\your\.venv\Lib\site-packages\wfastcgi.py"
           resourceType="Unspecified"
           requireAccess="Script" />
    </handlers>
  </system.webServer>

  <appSettings>
    <!-- Django settings module -->
    <add key="DJANGO_SETTINGS_MODULE" value="config.settings.production" />

    <!-- Optional: Override with ENV_NAME -->
    <!-- <add key="ENV_NAME" value="production" /> -->

    <!-- Secret key should be in .env file -->
  </appSettings>
</configuration>
```

**Important**: Update `scriptProcessor` to match your actual Python path:
- Example: `C:\inetpub\wwwroot\ITAM\.venv\Scripts\python.exe|C:\inetpub\wwwroot\ITAM\.venv\Lib\site-packages\wfastcgi.py`

---

## Step 3: Set Up IIS Site

1. Open **IIS Manager**
2. Right-click **Sites** → **Add Website**
3. Fill in:
   - **Site name**: ITAM
   - **Physical path**: `C:\inetpub\wwwroot\ITAM`
   - **Binding**: http, port 80 (or your preferred port)
   - **Hostname**: your-domain.com (or leave blank for all)
4. Click **OK**

---

## Step 4: Set Permissions

Grant IIS user access to your project folder:

```powershell
icacls "C:\inetpub\wwwroot\ITAM" /grant "IUSR:(OI)(CI)RX"
icacls "C:\inetpub\wwwroot\ITAM\media" /grant "IUSR:(OI)(CI)M"
icacls "C:\inetpub\wwwroot\ITAM\staticfiles" /grant "IUSR:(OI)(CI)R"
icacls "C:\inetpub\wwwroot\ITAM\db.sqlite3" /grant "IIS AppPool\ITAM:(OI)(CI)M"
```

---

## Step 5: Configure .env File

Create `.env` in your project root:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,your-server-ip,your-domain.com
```

---

## Step 6: Collect Static Files

```bash
python manage.py collectstatic --noinput --settings=config.settings.production
```

---

## Step 7: Run Migrations

```bash
python manage.py migrate --settings=config.settings.production
```

---

## Step 8: Test

Browse to:
- `http://localhost` (if using default binding)
- `http://your-server-ip`
- `http://your-domain.com`

---

## Troubleshooting

### 500 Internal Server Error
- Check IIS logs: `C:\inetpub\logs\LogFiles`
- Enable Failed Request Tracing in IIS
- Check `.env` file exists and is configured

### Static Files Not Loading
- Verify `staticfiles/` directory exists
- Check IIS static file handling
- Run `collectstatic` again

### Database Issues
- Ensure `IIS AppPool\YourSite` has write access to `db.sqlite3`
- Check SQLite file path in settings

---

## Alternative: Test Without IIS

```bash
python manage.py runserver 0.0.0.0:8000 --settings=config.settings.production
```

Browse to `http://your-server-ip:8000`

---

## Environment Variables

| Variable | Default | Description |
|-----------|---------|-------------|
| DJANGO_SETTINGS_MODULE | config.settings.production | Django settings |
| DEBUG | False | Debug mode |
| SECRET_KEY | (required) | Django secret key |

---

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` configured with actual hosts
- [ ] `.env` file not in Git
- [ ] IIS user has minimal required permissions
- [ ] HTTPS configured (update `web.config` for SSL)
- [ ] Static files served directly by IIS (not via Django)
