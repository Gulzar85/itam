# Windows Server Deployment Guide

## Deploying ITAM on Windows Server with IIS

### Prerequisites

1. **Windows Server 2019/2022**
2. **IIS (Internet Information Services)**
3. **Python 3.8+**
4. **URL Rewrite extension for IIS**
5. **Web Deploy (optional)**

---

## Step 1: Install Python

Download and install Python from https://www.python.org/downloads/

During installation, check:
- [x] Add Python to PATH
- [x] Install pip

---

## Step 2: Install Required Windows Features

Open PowerShell as Administrator:

```powershell
Install-WindowsFeature Web-Server -IncludeManagementTools
```

---

## Step 3: Setup Virtual Environment

```powershell
# Navigate to your web root (e.g., C:\inetpub\itam)
cd C:\inetpub\itam

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## Step 4: Configure Environment Variables

Create `.env` file in the project root:

```env
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-generate-using-openssl
ALLOWED_HOSTS=your-server-ip,your-domain.com
```

Generate a secure secret key:
```powershell
python -c "import secrets; print(secrets.token_hex(50))"
```

---

## Step 5: Database Setup

```powershell
# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
```

---

## Step 6: Install wfastcgi

```powershell
pip install wfastcgi
wfastcgi-enable
```

---

## Step 7: Configure IIS

1. Open **IIS Manager**
2. Create a new Site:
   - Site name: ITAM
   - Physical path: `C:\inetpub\itam`
   - Port: 80

3. Add a Web.config file:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <appSettings>
    <add key="PythonPath" value="C:\inetpub\itam\.venv;C:\inetpub\itam" />
    <add key="WSGI_HANDLER" value="wfastcgi.handler" />
    <add key="DJANGO_SETTINGS_MODULE" value="config.settings" />
  </appSettings>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI" 
           path="*" 
           verb="*" 
           modules="FastCgiModule" 
           scriptProcessor="C:\inetpub\itam\.venv\Scripts\python.exe|C:\inetpub\itam\.venv\Lib\site-packages\wfastcgi.py"
           resourceType="Unspecified" />
    </handlers>
    <staticContent>
      <mimeMap fileExtension=".svg" mimeType="image/svg+xml" />
    </staticContent>
    <rewrite>
      <rules>
        <rule name="Static Files" stopProcessing="true">
          <match url="^static/(.*)" />
          <action type="Rewrite" url="/staticfiles/$1" />
        </rule>
        <rule name="Media Files" stopProcessing="true">
          <match url="^media/(.*)" />
          <action type="Rewrite" url="/media/$1" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

4. Set Permissions:
   - Grant IIS_IUSRS read access to the project folder
   - Grant IUSR read access if needed

---

## Step 8: Test the Application

```powershell
# Test Django runs
python manage.py check

# Runserver to test
python manage.py runserver 0.0.0.0:8000
```

Visit http://localhost:8000

---

## Step 9: Troubleshooting

### Common Errors

**500 Error**
- Check event viewer for Python errors
- Verify .env file exists
- Check file permissions

**Static files not loading**
```powershell
python manage.py collectstatic --clear
```

**Database locked**
- Ensure no other process is using db.sqlite3
- Grant write permissions to IIS_IUSRS

---

## Quick Setup (Alternative - Development Mode)

For testing without full IIS setup:

```powershell
cd C:\inetpub\itam

# Create and activate venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver 0.0.0.0:8000
```

Then use IIS to create a reverse proxy to port 8000.

---

## Default Login Credentials

After initial setup:
- **Admin**: `admin` / `admin123`
- **Manager**: `manager` / `manager123`
- **Employee**: `employee1` / `employee123`

---

## Security Checklist for Production

- [ ] Set `DEBUG=False` in .env
- [ ] Use strong SECRET_KEY (50+ characters)
- [ ] Configure ALLOWED_HOSTS with your domain
- [ ] Set up HTTPS using Let's Encrypt or SSL certificate
- [ ] Restrict file permissions
- [ ] Configure proper logging
- [ ] Regular backups of database