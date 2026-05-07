# Remaining Tasks - ITAM Project

## 🚀 Immediate Actions Required

### 1. Install Dependencies
```powershell
# Option A: Use the setup script (recommended)
.\setup_dev.ps1

# Option B: Manual installation
pip install -r requirements.txt
```

### 2. Run Database Migrations
```bash
python manage.py makemigrations core accounts equipment requests notifications
python manage.py migrate
```

**Note:** The `SocialMediaLink` model was fixed, so a migration is required.

### 3. Create `.env` File
```bash
# Copy the example file
cp env_example.txt .env

# Edit .env and add your SECRET_KEY
# Generate a key with:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Test the Application
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## 🧪 Testing Checklist

### Critical Functionality:
- [ ] **Login/Logout** - Test rate limiting (5 attempts/minute)
- [ ] **File Uploads** - Upload equipment image (should reject files >2MB)
- [ ] **File Uploads** - Upload business logo (should validate image types)
- [ ] **Request Creation** - Create new equipment/repair request
- [ ] **Request Approval** - Manager approves/rejects request
- [ ] **Equipment Assignment** - Assign equipment to user
- [ ] **Notification System** - Check notifications are created
- [ ] **Reports** - Generate equipment/request reports

### Forms & Validation:
- [ ] All forms render with Tailwind classes
- [ ] Form validation works (required fields, email format, etc.)
- [ ] File upload validation rejects invalid files
- [ ] File upload accepts valid images

### Admin Interface:
- [ ] Jazzmin admin panel accessible
- [ ] Equipment CRUD operations work
- [ ] Request management works
- [ ] User management works

---

## 🔧 Production Deployment Steps

### 1. Set Up PostgreSQL Database
```bash
# Install PostgreSQL (if not installed)
# Windows: Download from https://www.postgresql.org/download/windows/

# Create database and user:
sudo -u postgres psql  # Linux/Mac
# OR use pgAdmin on Windows

CREATE DATABASE itam_db;
CREATE USER itam_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE itam_db TO itam_user;
```

### 2. Update `.env` for Production
```bash
ENV_NAME=production
DEBUG=False
SECRET_KEY=your-production-secret-key

# Database
DB_NAME=itam_db
DB_USER=itam_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Configure Static Files (using WhiteNoise)
Already configured in settings. Run:
```bash
python manage.py collectstatic
```

### 4. Set Up Redis (Optional - for better caching)
```bash
# Install Redis
# Windows: Use WSL2 or Memurai (Redis for Windows)
# Linux: sudo apt install redis-server

# Update CACHES in production.py to use Redis:
# CACHES = {
#     "default": {
#         "BACK_END": "django.core.cache.backends.redis.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#     }
# }
```

### 5. Deploy to PythonAnywhere (or your platform)
- Upload code
- Set up virtual environment
- Install requirements
- Configure `.env` with production settings
- Run migrations
- Set up static files
- Configure web app

---

## 📊 Performance Monitoring

### Monitor These Metrics:
1. **Database Queries** - Use Django Debug Toolbar in development
   ```bash
   pip install django-debug-toolbar
   # Add to INSTALLED_APPS and MIDDLEWARE (development only)
   ```

2. **Cache Hit Rate** - Monitor if caching is working
   ```python
   from django.core.cache import cache
   cache.set('test', 'value', 60)
   print(cache.get('test'))  # Should print 'value'
   ```

3. **Rate Limiting** - Check logs for rate limit warnings
   - Look in console output for rate limit messages

4. **File Upload Size** - Test uploading large files (>2MB should fail)

---

## 🐛 Common Issues & Solutions

### Issue: ModuleNotFoundError: No module named 'django_ratelimit'
**Solution:**
```bash
pip install django-ratelimit==4.1.0
```

### Issue: Migration errors after model changes
**Solution:**
```bash
# Delete migration files (except __init__.py) and recreate
rm equipment/migrations/000*.py
rm requests/migrations/000*.py
python manage.py makemigrations
python manage.py migrate
```

### Issue: Static files not loading
**Solution:**
```bash
python manage.py collectstatic --noinput
# Check STATIC_ROOT and STATICFILES_DIRS in settings
```

### Issue: PostgreSQL connection error
**Solution:**
- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `.env`
- Ensure database and user exist

---

## 📝 Code Quality Improvements (Optional)

### Add Tests
Create test cases in `tests.py` files:
```python
# Example: equipment/tests.py
from django.test import TestCase
from .models import Equipment

class EquipmentModelTest(TestCase):
    def test_equipment_creation(self):
        equipment = Equipment.objects.create(...)
        self.assertEqual(equipment.status, 'AVAILABLE')
```

### Add Django Debug Toolbar (Development)
```bash
pip install django-debug-toolbar
# Add to INSTALLED_APPS and MIDDLEWARE in development.py
```

### Set Up Logging Alerts
- Configure email alerts for ERROR level logs
- Use Sentry or similar service for production monitoring

---

## ✅ Final Verification

Before going to production:

- [ ] All tests pass
- [ ] Debug mode is OFF
- [ ] Secret key is secure
- [ ] HTTPS is enabled (SECURE_SSL_REDIRECT = True)
- [ ] Database is PostgreSQL (not SQLite)
- [ ] Static files are served correctly
- [ ] Media uploads work
- [ ] Rate limiting is active
- [ ] CSP headers are set
- [ ] Log rotation is working
- [ ] Backup strategy is in place

---

## 📞 Support

If you encounter issues:
1. Check the error logs in `logs/error.log`
2. Review `docs/SECURITY_FIXES.md` for details
3. Review `IMPLEMENTATION_SUMMARY.md` for changes made
4. Open an issue on the project repository

---

**🎉 Congratulations!** You've successfully implemented enterprise-grade security and code quality improvements to your ITAM project.
