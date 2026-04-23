# IT Asset Management (ITAM) System

A comprehensive Django-based IT Asset Management system for tracking, managing, and maintaining IT equipment and requests within an organization.

## Features

### Core Functionality
- **User Management**: Role-based access control (Employee, Manager, IT Admin)
- **Request Management**: Submit, approve, and track IT equipment requests
- **Equipment Inventory**: Complete CRUD operations for IT assets
- **Vendor Management**: Track suppliers and repair services
- **Notifications**: Real-time notifications for request updates
- **Audit Logging**: Complete audit trail for all actions

### Key Components
- **Dashboard**: Role-based dashboards with statistics and quick actions
- **Request Workflow**: PENDING → MANAGER_APPROVED → IT_RECEIVED → COMPLETED
- **Equipment Tracking**: Status management (Available, Assigned, Repairing, Damaged)
- **Warranty Management**: Track warranty periods and expiry dates
- **Search & Filtering**: Advanced search across all modules

## Technology Stack

- **Backend**: Django 5.0.6
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **Icons**: Lucide Icons
- **Forms**: Django Crispy Forms
- **Authentication**: Django Auth with custom user model

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd itam-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Populate initial data**
   ```bash
   python manage.py populate_initial_data
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Default Users

After running `populate_initial_data`, the following users are available:

- **Admin**: `admin` / `admin123` (IT Admin)
- **Manager**: `manager` / `manager123` (Manager)
- **Employee**: `employee1` / `employee123` (Employee)
- **Employee**: `employee2` / `employee123` (Employee)

## Project Structure

```
itam-system/
├── accounts/              # User management app
├── core/                  # Business info and settings
├── equipment/             # Equipment inventory management
├── notifications/         # Notification system
├── requests/              # Request management
├── services/              # Business logic services
├── static/                # Static files (CSS, JS)
├── templates/             # HTML templates
├── config/                # Django settings
└── manage.py
```

## Key Apps

### Accounts App
- Custom user model with roles
- Profile management
- Department management

### Equipment App
- Equipment CRUD operations
- Vendor management
- Brand and category management
- Status tracking

### Requests App
- Request creation and management
- Approval workflow
- Status tracking
- Audit logging

### Notifications App
- Real-time notifications
- Email notifications
- Notification templates

### Core App
- Business information
- Social media links
- System settings

## API Endpoints

The system provides REST API endpoints for integration:

- `/api/equipment/` - Equipment management
- `/api/requests/` - Request management
- `/api/users/` - User management
- `/api/notifications/` - Notification management

## Development

### Running Tests
```bash
python manage.py test
```

### Code Formatting
```bash
# Install black and isort
pip install black isort

# Format code
black .
isort .
```

### Database Schema
```bash
python manage.py makemigrations
python manage.py migrate
```

## Deployment

### Environment Variables
Create a `.env` file with:

```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Production Setup
1. Set `DEBUG=False` in settings
2. Configure PostgreSQL database
3. Set up email backend
4. Configure static files serving
5. Set up proper logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team.