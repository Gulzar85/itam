# IT Asset Management (ITAM) System

A comprehensive Django-based IT Asset Management system for tracking, managing, and maintaining IT equipment and requests within an organization.

## Features

### Core Functionality
- **User Management**: Role-based access control (Employee, IT Admin) with manager approval hierarchy
- **Request Management**: Submit, approve, and track IT equipment requests
- **Equipment Inventory**: Complete CRUD operations for IT assets with QR code generation
- **Vendor Management**: Track suppliers and repair services with performance ratings
- **Brand & Category Management**: Organize equipment by type and manufacturer
- **Notifications**: Real-time notifications for request updates
- **Audit Logging**: Complete audit trail for all actions
- **Reports & Analytics**: Comprehensive reporting with 7 specialized report types

### Key Components
- **Role-based Dashboard**: Different views for employees, managers, and IT admins
- **Request Workflow**: PENDING → MANAGER_APPROVED → IT_RECEIVED → IN_PROGRESS → COMPLETED
- **Equipment Tracking**: Status management (Available, Assigned, Repairing, Damaged)
- **Warranty Management**: Track warranty periods with expiry alerts
- **Maintenance Tracking**: Full repair lifecycle with vendor assignment and cost tracking
- **Search & Filtering**: Advanced search across all modules

## Technology Stack

- **Backend**: Django 6.0.4
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **Icons**: Lucide Icons
- **Forms**: Django Crispy Forms + Crispy Tailwind
- **Admin Theme**: Django Jazzmin
- **Static Files**: WhiteNoise
- **WSGI Server**: Gunicorn
- **Authentication**: Django Auth with custom user model

## Installation

### Prerequisites
- Python 3.12+
- pip
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd itam
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file**
   ```bash
   cp .env.example .env
   # Edit .env with your SECRET_KEY
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Populate sample data**
   ```bash
   python manage.py populate_data
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Default Users

After running `populate_data`:

- The seeder prints generated passwords to the console by default.
- To use fixed credentials in local/dev only, set:
  - `ITAM_SEED_ADMIN_PASSWORD`
  - `ITAM_SEED_MANAGER_PASSWORD`
  - `ITAM_SEED_EMPLOYEE_PASSWORD`

## Project Structure

```
itam/
├── accounts/              # User management & authentication
├── config/                # Django settings (base, development, production)
├── core/                  # Business info, settings, sequences
├── equipment/             # Equipment inventory, vendors, brands, categories
│   └── management/        # Management commands
├── notifications/         # Notification system
├── requests/              # Request management & workflow
├── services/              # Business logic layer
├── static/                # Static files (CSS, JS)
├── templates/             # HTML templates
├── media/                 # User-uploaded files
├── Procfile               # Production process file
├── runtime.txt            # Python runtime version
└── manage.py
```

## Models

### Accounts App
| Model | Description | Key Fields |
|-------|-------------|------------|
| `Department` | Organizational departments | `name` (unique) |
| `User` | Custom user model extending AbstractUser | `role`, `manager`, `email`, `phone_number`, `department` |

**User Roles**: `EMPLOYEE`, `IT_ADMIN`

### Equipment App
| Model | Description | Key Fields |
|-------|-------------|------------|
| `Vendor` | Equipment suppliers & repair services | `name`, `vendor_type`, `contact_person`, `phone`, `email`, `rating` |
| `Brand` | Equipment manufacturers | `name`, `support_contact`, `website` |
| `Category` | Equipment categories | `name`, `icon`, `description` |
| `Equipment` | IT assets inventory | `tracking_id`, `category`, `brand`, `model_number`, `serial_number`, `status`, `assigned_to`, `purchase_date`, `purchase_cost`, `warranty_expiry`, `qr_code`, `image` |
| `EquipmentLog` | Equipment status change audit trail | `equipment`, `action_by`, `old_status`, `new_status`, `remarks`, `timestamp` |
| `MaintenanceRecord` | Repair/maintenance tracking | `request`, `equipment`, `vendor`, `issue_description`, `estimated_cost`, `actual_cost`, `sent_date`, `expected_return_date`, `actual_return_date`, `status` |

**Equipment Status**: `AVAILABLE`, `ASSIGNED`, `REPAIRING`, `DAMAGED`

### Requests App
| Model | Description | Key Fields |
|-------|-------------|------------|
| `Request` | IT service requests | `request_id`, `user`, `request_type`, `priority`, `status`, `equipment`, `category_needed`, `brand_preference`, `reason`, `assigned_vendor` |
| `RequestLog` | Request status change audit trail | `request`, `action_by`, `old_status`, `new_status`, `remarks`, `timestamp` |
| `Assignment` | Equipment assignment records | `equipment`, `user`, `assigned_date`, `assigned_by`, `returned_date`, `notes` |

**Request Types**: `NEW`, `REPAIR`
**Request Priorities**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
**Request Status**: `PENDING`, `MANAGER_APPROVED`, `IT_RECEIVED`, `IN_PROGRESS`, `READY`, `COMPLETED`, `REJECTED`

### Notifications App
| Model | Description | Key Fields |
|-------|-------------|------------|
| `Notification` | User notifications | `recipient`, `notification_type`, `title`, `message`, `priority`, `is_read`, `is_archived`, `read_at` |
| `NotificationTemplate` | Notification message templates | `notification_type`, `subject_template`, `message_template`, `is_active` |

**Notification Types**: `REQUEST_CREATED`, `REQUEST_APPROVED`, `REQUEST_REJECTED`, `REQUEST_COMPLETED`, `EQUIPMENT_ASSIGNED`, `EQUIPMENT_RETURNED`, `MAINTENANCE_DUE`, `WARRANTY_EXPIRING`, `SYSTEM_ALERT`, `ACTION_PERFORMED`

### Core App
| Model | Description | Key Fields |
|-------|-------------|------------|
| `SequenceCounter` | Atomic counter for sequential ID generation | `key`, `year`, `value` |
| `BusinessInfo` | Company information & branding | `name`, `logo`, `description`, `address`, `contact_email`, `contact_phone`, `website`, `primary_color`, `secondary_color`, `accent_color` |
| `SocialMediaLink` | Social media links for the company | `business`, `platform`, `url` |

## Views

### Accounts App (`accounts/views.py`)
| View | Type | Access | Description |
|------|------|--------|-------------|
| `ProfileDetailView` | DetailView | LoginRequired | Display user profile |
| `ProfileUpdateView` | UpdateView | LoginRequired | Edit user profile |
| `CustomPasswordChangeView` | View | LoginRequired | Change password |
| `RegisterView` | CreateView | ITAdminOnly | Register new users |
| `CustomPasswordResetView` | View | Public | Password reset request |
| `CustomPasswordResetConfirmView` | View | Public | Password reset confirm |

### Equipment App (`equipment/views.py`)
| View | Type | Access | Description |
|------|------|--------|-------------|
| `EquipmentListView` | ListView | LoginRequired | List all equipment with filtering |
| `EquipmentDetailView` | DetailView | LoginRequired | Equipment detail view |
| `EquipmentCreateView` | CreateView | ITAdminOnly | Create new equipment |
| `EquipmentUpdateView` | UpdateView | ITAdminOnly | Update equipment |
| `EquipmentDeleteView` | DeleteView | ITAdminOnly | Delete equipment |
| `EquipmentStatusUpdateView` | View | ITAdminOnly | AJAX status update |
| `EquipmentBulkActionView` | View | ITAdminOnly | Bulk operations |
| `EquipmentExportView` | View | ITAdminOnly | Export to CSV |
| `VendorListView` | ListView | ITAdminOnly | List vendors |
| `VendorDetailView` | DetailView | ITAdminOnly | Vendor details |
| `VendorCreateView` | CreateView | ITAdminOnly | Create vendor |
| `VendorUpdateView` | UpdateView | ITAdminOnly | Update vendor |
| `VendorDeleteView` | DeleteView | ITAdminOnly | Delete vendor |
| `BrandListView` | ListView | ITAdminOnly | List brands |
| `BrandDetailView` | DetailView | ITAdminOnly | Brand details |
| `BrandCreateView` | CreateView | ITAdminOnly | Create brand |
| `BrandUpdateView` | UpdateView | ITAdminOnly | Update brand |
| `BrandDeleteView` | DeleteView | ITAdminOnly | Delete brand |
| `CategoryListView` | ListView | ITAdminOnly | List categories |
| `CategoryDetailView` | DetailView | ITAdminOnly | Category details |
| `CategoryCreateView` | CreateView | ITAdminOnly | Create category |
| `CategoryUpdateView` | UpdateView | ITAdminOnly | Update category |
| `CategoryDeleteView` | DeleteView | ITAdminOnly | Delete category |
| `DashboardReportView` | TemplateView | ITAdminOnly | Analytics dashboard report |
| `ComprehensiveReportView` | TemplateView | ITAdminOnly | Comprehensive equipment report |
| `MaintenanceHistoryReportView` | TemplateView | ITAdminOnly | Maintenance history report |
| `RequestSummaryReportView` | TemplateView | ITAdminOnly | Request summary report |
| `VendorPerformanceReportView` | TemplateView | ITAdminOnly | Vendor performance report |
| `DepartmentDistributionReportView` | TemplateView | ITAdminOnly | Department distribution report |
| `RequestTurnaroundReportView` | TemplateView | ITAdminOnly | Request turnaround report |

### Requests App (`requests/views.py`)
| View | Type | Access | Description |
|------|------|--------|-------------|
| `MyEquipmentView` | ListView | LoginRequired | View assigned equipment (user-specific) |
| `RequestDashboardView` | ListView | LoginRequired | Main dashboard with role-based visibility |
| `RequestCreateView` | CreateView | LoginRequired | Create new request |
| `RequestActionView` | View | ManagerOrAdmin | Approve/reject requests (AJAX) |
| `RequestDetailView` | DetailView | LoginRequired | Request details with actions |
| `AssignmentCreateView` | CreateView | ITAdminOnly | Assign equipment to user |
| `RequestAssignmentView` | View | ITAdminOnly | Assign equipment via request (AJAX) |
| `ManagerApprovalView` | ListView | ManagerOrAdmin | Manager approval queue |
| `ProcessMaintenanceView` | View | ITAdminOnly | Send equipment for repair (AJAX) |
| `CompleteMaintenanceView` | View | ITAdminOnly | Complete repair process (AJAX) |

### Notifications App (`notifications/views.py`)
| View | Type | Access | Description |
|------|------|--------|-------------|
| `NotificationListView` | ListView | LoginRequired | List user notifications |
| `NotificationDetailView` | DetailView | LoginRequired | Notification details |
| `MarkAsReadView` | View | LoginRequired | Mark notification as read (AJAX) |
| `MarkAllAsReadView` | View | LoginRequired | Mark all as read (AJAX) |
| `ArchiveNotificationView` | View | LoginRequired | Archive notification (AJAX) |
| `NotificationCountView` | View | LoginRequired | Get unread count (AJAX) |
| `DeleteNotificationView` | View | LoginRequired | Delete notification (AJAX) |

### Core App (`core/views.py`)
| View | Type | Access | Description |
|------|------|--------|-------------|
| `GlobalSearchView` | View | LoginRequired | Global search endpoint (AJAX) |
| `BusinessInfoDetailView` | DetailView | ITAdminOnly | View business info |
| `BusinessInfoUpdateView` | UpdateView | ITAdminOnly | Edit business info |
| `SocialMediaListView` | ListView | ITAdminOnly | List social media links |
| `SocialMediaCreateView` | CreateView | ITAdminOnly | Add social media link |
| `SocialMediaUpdateView` | UpdateView | ITAdminOnly | Edit social media link |
| `SocialMediaDeleteView` | DeleteView | ITAdminOnly | Delete social media link |

## URL Configuration

### Root URLs (`config/urls.py`)
| Pattern | App | Description |
|---------|-----|-------------|
| `/` | requests | Dashboard |
| `/admin/` | admin | Django Admin |
| `/inventory/` | equipment | Equipment management |
| `/accounts/` | accounts | Authentication & profile |
| `/notifications/` | notifications | Notifications |
| `/settings/` | core | Business settings |
| `/requests/` | requests | Request management |
| `/api/search/` | core | Global search API |

### Accounts URLs (`/accounts/`)
| Pattern | Name | Description |
|---------|------|-------------|
| `login/` | `accounts:login` | Login page |
| `logout/` | `accounts:logout` | Logout |
| `register/` | `accounts:register` | Register user (IT Admin) |
| `password-reset/` | `accounts:password_reset` | Password reset |
| `password-reset/done/` | `accounts:password_reset_done` | Reset sent confirmation |
| `password-reset-confirm/<uidb64>/<token>/` | `accounts:password_reset_confirm` | Reset password |
| `password-reset-complete/` | `accounts:password_reset_complete` | Reset complete |
| `profile/` | `accounts:profile` | View profile |
| `profile/edit/` | `accounts:profile_edit` | Edit profile |
| `profile/change-password/` | `accounts:change_password` | Change password |

### Equipment URLs (`/inventory/`)
| Pattern | Name | Description |
|---------|------|-------------|
| `equipment/` | `equipment:equipment_list` | Equipment list |
| `equipment/<uuid:pk>/` | `equipment:equipment_detail` | Equipment detail |
| `equipment/create/` | `equipment:equipment_create` | Create equipment |
| `equipment/<uuid:pk>/update/` | `equipment:equipment_update` | Update equipment |
| `equipment/<uuid:pk>/delete/` | `equipment:equipment_delete` | Delete equipment |
| `equipment/<uuid:pk>/status/` | `equipment:update_status` | Update status (AJAX) |
| `equipment/bulk-action/` | `equipment:equipment_bulk_action` | Bulk actions |
| `equipment/export/` | `equipment:equipment_export` | Export CSV |
| `vendors/` | `equipment:vendor_list` | Vendor list |
| `vendors/<uuid:pk>/` | `equipment:vendor_detail` | Vendor detail |
| `vendors/create/` | `equipment:vendor_create` | Create vendor |
| `vendors/<uuid:pk>/update/` | `equipment:vendor_update` | Update vendor |
| `vendors/<uuid:pk>/delete/` | `equipment:vendor_delete` | Delete vendor |
| `brands/` | `equipment:brand_list` | Brand list |
| `brands/<uuid:pk>/` | `equipment:brand_detail` | Brand detail |
| `brands/create/` | `equipment:brand_create` | Create brand |
| `brands/<uuid:pk>/update/` | `equipment:brand_update` | Update brand |
| `brands/<uuid:pk>/delete/` | `equipment:brand_delete` | Delete brand |
| `categories/` | `equipment:category_list` | Category list |
| `categories/<uuid:pk>/` | `equipment:category_detail` | Category detail |
| `categories/create/` | `equipment:category_create` | Create category |
| `categories/<uuid:pk>/update/` | `equipment:category_update` | Update category |
| `categories/<uuid:pk>/delete/` | `equipment:category_delete` | Delete category |
| `list/` | `equipment:inventory_list` | Legacy inventory list |
| `dashboard/report/` | `equipment:dashboard_report` | Analytics report |
| `reports/comprehensive/` | `equipment:comprehensive_report` | Comprehensive report |
| `reports/maintenance/` | `equipment:maintenance_report` | Maintenance report |
| `reports/requests/` | `equipment:request_summary_report` | Request summary |
| `reports/vendor-performance/` | `equipment:vendor_performance_report` | Vendor performance |
| `reports/department-distribution/` | `equipment:department_report` | Department distribution |
| `reports/request-turnaround/` | `equipment:turnaround_report` | Turnaround report |

### Requests URLs (`/requests/`)
| Pattern | Name | Description |
|---------|------|-------------|
| `/` | `dashboard` | Request dashboard |
| `my-equipment/` | `requests:my_equipment` | My assigned equipment |
| `new/` | `requests:create` | Create request |
| `approvals/` | `requests:manager_approvals` | Manager approvals |
| `<uuid:pk>/` | `requests:detail` | Request detail |
| `action/<uuid:pk>/` | `requests:update_action` | Approve/reject (AJAX) |
| `<uuid:pk>/assign/` | `requests:assign_equipment` | Assign equipment (AJAX) |
| `assign-new/` | `requests:equipment_assign` | General assignment form |
| `<uuid:pk>/process-maintenance/` | `requests:process_maintenance` | Send to repair (AJAX) |
| `<uuid:pk>/complete-maintenance/` | `requests:complete_maintenance` | Complete repair (AJAX) |

### Notifications URLs (`/notifications/`)
| Pattern | Name | Description |
|---------|------|-------------|
| `/` | `notifications:list` | Notification list |
| `<uuid:pk>/` | `notifications:detail` | Notification detail |
| `mark-read/<uuid:pk>/` | `notifications:mark_read` | Mark as read (AJAX) |
| `mark-all-read/` | `notifications:mark_all_read` | Mark all read (AJAX) |
| `archive/<uuid:pk>/` | `notifications:archive` | Archive (AJAX) |
| `count/` | `notifications:count` | Unread count (AJAX) |
| `delete/<uuid:pk>/` | `notifications:delete` | Delete (AJAX) |

### Core URLs (`/settings/`)
| Pattern | Name | Description |
|---------|------|-------------|
| `business/` | `core:business_info` | Business info |
| `business/edit/` | `core:business_info_update` | Edit business info |
| `social-media/` | `core:social_media_list` | Social media links |
| `social-media/add/` | `core:social_media_create` | Add link |
| `social-media/<int:pk>/edit/` | `core:social_media_update` | Edit link |
| `social-media/<int:pk>/delete/` | `core:social_media_delete` | Delete link |

## Templates

### Base Templates
| Template | Description |
|----------|-------------|
| `base.html` | Main layout with sidebar, navbar, messages |

### Includes
| Template | Description |
|----------|-------------|
| `includes/sidebar.html` | Navigation sidebar with role-based links |
| `includes/navbar.html` | Top navigation with search, notifications, user menu |
| `includes/breadcrumbs.html` | Breadcrumb navigation |
| `includes/status_badge.html` | Status badge component |
| `includes/timeline.html` | Activity timeline component |
| `includes/stats_cards.html` | Statistics cards component |
| `includes/pagination.html` | Pagination component |
| `includes/search.html` | Search component |
| `includes/empty_state.html` | Empty state placeholder |
| `includes/form_errors.html` | Form error display |
| `includes/remarks_modal.html` | Remarks input modal |

### Accounts Templates
| Template | Description |
|----------|-------------|
| `accounts/login.html` | Login page |
| `accounts/register.html` | User registration (IT Admin) |
| `accounts/profile.html` | Profile view |
| `accounts/profile_edit.html` | Profile edit form |
| `accounts/change_password.html` | Change password form |
| `accounts/password_reset.html` | Password reset request |
| `accounts/password_reset_done.html` | Reset email sent |
| `accounts/password_reset_confirm.html` | Reset password form |
| `accounts/password_reset_complete.html` | Reset complete |

### Equipment Templates
| Template | Description |
|----------|-------------|
| `equipment/equipment_list.html` | Equipment grid list |
| `equipment/equipment_detail.html` | Equipment detail view |
| `equipment/equipment_form.html` | Create/edit equipment form |
| `equipment/equipment_confirm_delete.html` | Delete confirmation |
| `equipment/vendor_list.html` | Vendor list |
| `equipment/vendor_detail.html` | Vendor detail |
| `equipment/vendor_form.html` | Vendor form |
| `equipment/vendor_confirm_delete.html` | Vendor delete |
| `equipment/brand_list.html` | Brand list |
| `equipment/brand_detail.html` | Brand detail |
| `equipment/brand_form.html` | Brand form |
| `equipment/brand_confirm_delete.html` | Brand delete |
| `equipment/category_list.html` | Category list |
| `equipment/category_detail.html` | Category detail |
| `equipment/category_form.html` | Category form |
| `equipment/category_confirm_delete.html` | Category delete |
| `equipment/inventory_list.html` | Legacy inventory view |

### Requests Templates
| Template | Description |
|----------|-------------|
| `requests/request_form.html` | Create request form |
| `requests/request_detail.html` | Request detail with actions |
| `requests/my_equipment.html` | User's assigned equipment |
| `requests/assignment_form.html` | Equipment assignment form |
| `requests/manager_approvals.html` | Manager approval queue |

### Notifications Templates
| Template | Description |
|----------|-------------|
| `notifications/notification_list.html` | Notification list |
| `notifications/notification_detail.html` | Notification detail |

### Dashboard & Reports Templates
| Template | Description |
|----------|-------------|
| `dashboard/index.html` | Main dashboard |
| `dashboard/reports.html` | Analytics report |
| `reports/comprehensive.html` | Comprehensive equipment report |
| `reports/maintenance_history.html` | Maintenance history report |
| `reports/request_summary.html` | Request summary report |
| `reports/vendor_performance.html` | Vendor performance report |
| `reports/department_distribution.html` | Department distribution report |
| `reports/request_turnaround.html` | Turnaround analysis report |

### Core Templates
| Template | Description |
|----------|-------------|
| `core/business_info.html` | Business info view |
| `core/business_info_form.html` | Edit business info |
| `core/social_media_list.html` | Social media links list |
| `core/social_media_form.html` | Add/edit social link |
| `core/social_media_confirm_delete.html` | Delete social link |

## Services Layer

### `services/equipment_service.py`
| Method | Description |
|--------|-------------|
| `generate_tracking_id()` | Generate unique equipment tracking ID |
| `generate_qr_code(equipment)` | Generate QR code for equipment |
| `update_equipment_status()` | Update status with audit logging |

### `services/request_service.py`
| Method | Description |
|--------|-------------|
| `create_new_request()` | Create request with notification |
| `update_request_status()` | Update status with logging & notifications |

### `services/permissions.py`
| Mixin | Description |
|-------|-------------|
| `ITAdminRequiredMixin` | Restrict access to IT Admin role |
| `ManagerOrAdminRequiredMixin` | Allow managers and IT admins |

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts equipment requests notifications core

# Run with verbosity
python manage.py test --verbosity=2
```

**Test Coverage**: 102 tests across all apps (models, views, permissions, services)

## Deployment

### Production Settings
```bash
# .env file
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,itam.pythonanywhere.com
```

### Run with Gunicorn
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### PythonAnywhere Deployment
1. Upload code or pull from GitHub
2. Configure WSGI file to use `config.settings.production`
3. Set up virtual environment
4. Run `collectstatic`
5. Configure static files mappings

## License

MIT License
