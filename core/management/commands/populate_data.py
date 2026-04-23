from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import Department
from equipment.models import Category, Brand, Vendor, Equipment, EquipmentLog
from core.models import BusinessInfo, SocialMediaLink
from notifications.models import Notification, NotificationTemplate
from requests.models import Request, RequestLog, Assignment
import random
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate comprehensive sample data for ITAM system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--regenerate-qr',
            action='store_true',
            help='Regenerate QR codes for all equipment',
        )
        parser.add_argument(
            '--minimal',
            action='store_true',
            help='Create minimal data (5 equipment, 3 users)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Populating ITAM system data...')

        departments = self.create_departments()
        it_admin, managers, employees = self.create_users(departments)
        categories = self.create_categories()
        brands = self.create_brands()
        vendors = self.create_vendors()
        equipment_list = self.create_equipment(categories, brands, vendors, employees, options['minimal'])

        self.create_business_info()
        self.create_social_media_links()
        self.create_notification_templates()

        requests_list = self.create_requests(employees, categories, brands, vendors, equipment_list, it_admin)
        self.create_assignments(equipment_list, employees, it_admin)
        self.create_equipment_logs(equipment_list, it_admin)
        self.create_notifications(employees, it_admin, requests_list)

        if options['regenerate_qr']:
            self.regenerate_qr_codes()

        self.print_summary(equipment_list, employees, requests_list)

    def create_departments(self):
        departments = {}
        dept_names = [
            'IT', 'HR', 'Finance', 'Marketing', 'Operations', 
            'Sales', 'Engineering', 'Customer Support', 'Legal', 'Research'
        ]
        for name in dept_names:
            dept, _ = Department.objects.get_or_create(name=name)
            departments[name] = dept
        self.stdout.write(f'  Created {len(departments)} departments')
        return departments

    def create_users(self, departments):
        it_admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@company.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.IS_IT_ADMIN,
                'department': departments['IT'],
                'is_staff': True,
                'is_superuser': True
            }
        )
        it_admin.set_password('admin123')
        it_admin.save()

        managers = []
        manager_data = [
            ('manager_hr', 'Sarah', 'Johnson', 'manager.hr@company.com', departments['HR']),
            ('manager_finance', 'Michael', 'Chen', 'manager.finance@company.com', departments['Finance']),
            ('manager_it', 'David', 'Wilson', 'manager.it@company.com', departments['IT']),
            ('manager_marketing', 'Emily', 'Davis', 'manager.marketing@company.com', departments['Marketing']),
        ]
        for username, first, last, email, dept in manager_data:
            manager, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'role': User.IS_MANAGER,
                    'department': dept
                }
            )
            manager.set_password('manager123')
            manager.save()
            managers.append(manager)

        employees = []
        employee_data = [
            ('alice', 'Alice', 'Johnson', 'alice@company.com', departments['HR'], managers[0]),
            ('bob', 'Bob', 'Smith', 'bob@company.com', departments['Finance'], managers[1]),
            ('charlie', 'Charlie', 'Brown', 'charlie@company.com', departments['Marketing'], managers[0]),
            ('david', 'David', 'Wilson', 'david@company.com', departments['IT'], managers[2]),
            ('emma', 'Emma', 'Davis', 'emma@company.com', departments['Sales'], managers[0]),
            ('frank', 'Frank', 'Miller', 'frank@company.com', departments['Engineering'], managers[2]),
            ('grace', 'Grace', 'Taylor', 'grace@company.com', departments['Operations'], managers[1]),
            ('henry', 'Henry', 'Anderson', 'henry@company.com', departments['IT'], managers[2]),
            ('ivy', 'Ivy', 'Thomas', 'ivy@company.com', departments['Customer Support'], managers[0]),
            ('jack', 'Jack', 'Robinson', 'jack@company.com', departments['Finance'], managers[1]),
            ('kate', 'Kate', 'White', 'kate@company.com', departments['Marketing'], managers[3]),
            ('leo', 'Leo', 'Garcia', 'leo@company.com', departments['Sales'], managers[0]),
        ]
        for username, first, last, email, dept, manager in employee_data:
            emp, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'role': User.IS_EMPLOYEE,
                    'department': dept,
                    'manager': manager,
                    'phone_number': f'+1234567{random.randint(1000, 9999)}'
                }
            )
            emp.set_password('employee123')
            emp.save()
            employees.append(emp)

        self.stdout.write(f'  Created 1 IT Admin, {len(managers)} managers, {len(employees)} employees')
        return it_admin, managers, employees

    def create_categories(self):
        categories = {}
        cat_data = [
            ('Laptop', 'laptop', 'Portable computing device'),
            ('Desktop', 'monitor', 'Fixed workstation computer'),
            ('Printer', 'printer', 'Document printing device'),
            ('Monitor', 'display', 'Visual display unit'),
            ('Keyboard', 'keyboard', 'Input device'),
            ('Mouse', 'mouse', 'Pointing device'),
            ('Headphones', 'headphones', 'Audio output device'),
            ('Webcam', 'video', 'Video capture device'),
            ('Projector', 'presentation', 'Projection device'),
            ('Tablet', 'tablet', 'Touchscreen portable device'),
            ('Phone', 'phone', 'Communication device'),
            ('Router', 'router', 'Network device'),
            ('Scanner', 'scan', 'Document scanning device'),
            ('UPS', 'battery', 'Uninterruptible power supply'),
            ('Server', 'server', 'Data processing unit'),
        ]
        for name, icon, desc in cat_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'description': desc}
            )
            categories[name] = cat
        self.stdout.write(f'  Created {len(categories)} categories')
        return categories

    def create_brands(self):
        brands = {}
        brand_data = [
            ('Dell', '+1800555010', 'https://dell.com', 'Leading computer hardware manufacturer'),
            ('HP', '+1800474100', 'https://hp.com', 'Personal computing solutions'),
            ('Lenovo', '+1855255960', 'https://lenovo.com', 'Business and consumer laptops'),
            ('Apple', '+1800697463', 'https://apple.com', 'Premium consumer electronics'),
            ('Samsung', '+1800726786', 'https://samsung.com', 'Electronics and mobile devices'),
            ('Logitech', '+1800951202', 'https://logitech.com', 'Computer peripherals'),
            ('Cisco', '+1800553083', 'https://cisco.com', 'Networking equipment'),
            ('Microsoft', '+1800702600', 'https://microsoft.com', 'Software and hardware'),
            ('Asus', '+1800286120', 'https://asus.com', 'Motherboards and laptops'),
            ('Acer', '+18662212273', 'https://acer.com', 'Budget-friendly computers'),
            ('LG', '+1800243000', 'https://lg.com', 'Electronics and displays'),
            ('Sony', '+1800345776', 'https://sony.com', 'Electronics and audio'),
            ('Bose', '+1800869100', 'https://bose.com', 'Audio equipment'),
            ('Epson', '+1800463666', 'https://epson.com', 'Printers and projectors'),
            ('APC', '+1800802828', 'https://apc.com', 'Power protection'),
            ('Netgear', '+1800211611', 'https://netgear.com', 'Networking equipment'),
            ('Canon', '+1800652770', 'https://canon.com', 'Imaging equipment'),
        ]
        for name, contact, website, desc in brand_data:
            brand, _ = Brand.objects.get_or_create(
                name=name,
                defaults={
                    'support_contact': contact, 
                    'website': website,
                }
            )
            brands[name] = brand
        self.stdout.write(f'  Created {len(brands)} brands')
        return brands

    def create_vendors(self):
        vendors = {}
        vendor_data = [
            ('Tech Solutions Inc.', 'Mike Johnson', '+1234567890', 'mike@techsolutions.com', 'BOTH', 5, '123 Tech Street, Silicon Valley, CA'),
            ('Global Electronics', 'Sarah Davis', '+1234567891', 'sarah@globalelec.com', 'SUPPLIER', 4, '456 Commerce Ave, New York, NY'),
            ('Repair Masters', 'Tom Wilson', '+1234567892', 'tom@repairmasters.com', 'REPAIR', 5, '789 Fixer Lane, Austin, TX'),
            ('Quick Fix Services', 'Jane Smith', '+1234567893', 'jane@quickfix.com', 'REPAIR', 4, '321 Quick St, Chicago, IL'),
            ('Office Depot', 'Bill Johnson', '+1234567894', 'bill@officedepot.com', 'SUPPLIER', 3, '654 Office Blvd, Seattle, WA'),
            ('Enterprise IT Supply', 'Robert Brown', '+1234567895', 'robert@enterpriseit.com', 'BOTH', 5, '987 Enterprise Way, San Francisco, CA'),
        ]
        for name, person, phone, email, vtype, rating, addr in vendor_data:
            vendor, _ = Vendor.objects.get_or_create(
                name=name,
                defaults={
                    'contact_person': person,
                    'phone': phone,
                    'email': email,
                    'vendor_type': vtype,
                    'rating': rating,
                    'address': addr
                }
            )
            vendors[name] = vendor
        self.stdout.write(f'  Created {len(vendors)} vendors')
        return vendors

    def create_equipment(self, categories, brands, vendors, employees, minimal=False):
        all_brands = dict(brands)
        all_brands.update({
            'LG': brands.get('LG') or brands.get('Dell'),
            'Sony': brands.get('Sony') or brands.get('Apple'),
            'Bose': brands.get('Bose') or brands.get('Sony', list(brands.values())[0]),
            'Epson': brands.get('Epson') or brands.get('HP'),
            'APC': brands.get('APC') or brands.get('Dell'),
            'Netgear': brands.get('Netgear') or brands.get('Cisco'),
            'Canon': brands.get('Canon') or brands.get('HP'),
            'Microsoft': brands.get('Microsoft') or brands.get('Dell'),
        })
        
        if minimal:
            equip_data = [
                ('Laptop', 'Dell', 'Latitude 5520', 'DELL-NB-001', 'AVAILABLE', None),
                ('Laptop', 'HP', 'EliteBook 840', 'HP-NB-001', 'ASSIGNED', employees[0]),
                ('Desktop', 'Lenovo', 'ThinkCentre M70', 'LENOVO-DT-001', 'AVAILABLE', None),
                ('Printer', 'HP', 'LaserJet Pro M182nw', 'HP-PRT-001', 'REPAIRING', None, vendors['Repair Masters']),
                ('Monitor', 'Samsung', 'UR59C', 'SAMSUNG-MON-001', 'AVAILABLE', None),
            ]
        else:
            equip_data = [
                ('Laptop', 'Dell', 'Latitude 5520', 'DELL-NB-001', 'AVAILABLE', None),
                ('Laptop', 'Dell', 'Latitude 5520', 'DELL-NB-002', 'AVAILABLE', None),
                ('Laptop', 'Dell', 'Latitude 5420', 'DELL-NB-003', 'AVAILABLE', None),
                ('Laptop', 'HP', 'EliteBook 840', 'HP-NB-001', 'ASSIGNED', employees[0]),
                ('Laptop', 'HP', 'EliteBook 840', 'HP-NB-002', 'AVAILABLE', None),
                ('Laptop', 'Apple', 'MacBook Pro 14"', 'APPLE-NB-001', 'AVAILABLE', None),
                ('Laptop', 'Apple', 'MacBook Air M2', 'APPLE-NB-002', 'ASSIGNED', employees[1]),
                ('Laptop', 'Lenovo', 'ThinkPad X1 Carbon', 'LENOVO-NB-001', 'ASSIGNED', employees[2]),
                ('Laptop', 'Lenovo', 'ThinkPad T14', 'LENOVO-NB-002', 'AVAILABLE', None),
                ('Laptop', 'Asus', 'ZenBook Pro 16X', 'ASUS-NB-001', 'AVAILABLE', None),
                ('Desktop', 'Dell', 'OptiPlex 7090', 'DELL-DT-001', 'AVAILABLE', None),
                ('Desktop', 'HP', 'ProDesk 400', 'HP-DT-001', 'AVAILABLE', None),
                ('Desktop', 'Lenovo', 'ThinkCentre M70', 'LENOVO-DT-001', 'AVAILABLE', None),
                ('Monitor', 'Dell', 'UltraSharp U2722D', 'DELL-MON-001', 'AVAILABLE', None),
                ('Monitor', 'Dell', 'UltraSharp U2722D', 'DELL-MON-002', 'AVAILABLE', None),
                ('Monitor', 'Samsung', 'Odyssey G7', 'SAMSUNG-MON-001', 'ASSIGNED', employees[3]),
                ('Monitor', 'Samsung', 'Odyssey G7', 'SAMSUNG-MON-002', 'AVAILABLE', None),
                ('Monitor', 'LG', '27UK850-W', 'LG-MON-001', 'AVAILABLE', None),
                ('Printer', 'HP', 'LaserJet Pro M404dn', 'HP-PRT-001', 'AVAILABLE', None),
                ('Printer', 'HP', 'LaserJet Pro M404dn', 'HP-PRT-002', 'REPAIRING', None, vendors['Repair Masters']),
                ('Printer', 'Canon', 'ImageRunner 2520', 'CANON-PRT-001', 'AVAILABLE', None),
                ('Keyboard', 'Logitech', 'MX Keys', 'LOGI-KB-001', 'AVAILABLE', None),
                ('Keyboard', 'Logitech', 'MX Keys', 'LOGI-KB-002', 'ASSIGNED', employees[4]),
                ('Keyboard', 'Logitech', 'MX Keys Advanced', 'LOGI-KB-003', 'AVAILABLE', None),
                ('Keyboard', 'Microsoft', 'Surface Keyboard', 'MS-KB-001', 'AVAILABLE', None),
                ('Mouse', 'Logitech', 'MX Master 3', 'LOGI-MO-001', 'AVAILABLE', None),
                ('Mouse', 'Logitech', 'MX Master 3', 'LOGI-MO-002', 'ASSIGNED', employees[5]),
                ('Mouse', 'Logitech', 'MX Master 3', 'LOGI-MO-003', 'AVAILABLE', None),
                ('Mouse', 'Apple', 'Magic Mouse', 'APPLE-MO-001', 'AVAILABLE', None),
                ('Headphones', 'Apple', 'AirPods Pro', 'AP-HP-001', 'AVAILABLE', None),
                ('Headphones', 'Apple', 'AirPods Pro', 'AP-HP-002', 'ASSIGNED', employees[6]),
                ('Headphones', 'Sony', 'WH-1000XM5', 'SONY-HP-001', 'AVAILABLE', None),
                ('Headphones', 'Bose', 'QuietComfort 45', 'BOSE-HP-001', 'AVAILABLE', None),
                ('Webcam', 'Logitech', 'C920', 'LOGI-WC-001', 'AVAILABLE', None),
                ('Webcam', 'Logitech', 'Brio 4K', 'LOGI-WC-002', 'AVAILABLE', None),
                ('Webcam', 'Microsoft', 'LifeCam HD-3000', 'MS-WC-001', 'AVAILABLE', None),
                ('Tablet', 'Apple', 'iPad Pro 12.9"', 'APPLE-TB-001', 'AVAILABLE', None),
                ('Tablet', 'Apple', 'iPad Air', 'APPLE-TB-002', 'ASSIGNED', employees[7]),
                ('Tablet', 'Samsung', 'Galaxy Tab S8', 'SAMSUNG-TB-001', 'AVAILABLE', None),
                ('Router', 'Cisco', 'Meraki MR46', 'CISCO-RO-001', 'AVAILABLE', None),
                ('Router', 'Cisco', 'Catalyst 9200', 'CISCO-RO-002', 'AVAILABLE', None),
                ('Router', 'Netgear', 'Nighthawk AX12', 'NETGEAR-RO-001', 'AVAILABLE', None),
                ('Phone', 'Samsung', 'Galaxy S23', 'SAMSUNG-PH-001', 'ASSIGNED', employees[8]),
                ('Phone', 'Apple', 'iPhone 14 Pro', 'APPLE-PH-001', 'ASSIGNED', employees[9]),
                ('Scanner', 'Epson', 'WorkForce ES-400', 'EPSON-SC-001', 'AVAILABLE', None),
                ('UPS', 'APC', 'Smart-UPS 1500VA', 'APC-UPS-001', 'AVAILABLE', None),
                ('Server', 'Dell', 'PowerEdge R750', 'DELL-SRV-001', 'AVAILABLE', None),
                ('Projector', 'Epson', 'PowerLite 2250U', 'EPSON-PRJ-001', 'AVAILABLE', None),
            ]

        equipment_list = []
        for data in equip_data:
            cat_name, brand_name, model, serial = data[0], data[1], data[2], data[3]
            status = data[4]
            assigned = data[5] if len(data) > 5 and data[5] else None
            repair_vendor = data[6] if len(data) > 6 and data[6] else None
            
            purchase_cost = random.randint(500, 5000)
            
            eq, created = Equipment.objects.get_or_create(
                serial_number=serial,
                defaults={
                    'category': categories[cat_name],
                    'brand': all_brands.get(brand_name, brands['Dell']),
                    'model_number': model,
                    'original_vendor': vendors['Tech Solutions Inc.'],
                    'status': status,
                    'assigned_to': assigned,
                    'current_repair_vendor': repair_vendor,
                    'purchase_date': date.today() - timedelta(days=random.randint(30, 730)),
                    'purchase_cost': purchase_cost,
                    'warranty_expiry': date.today() + timedelta(days=random.randint(30, 730)),
                }
            )
            equipment_list.append(eq)

        self.stdout.write(f'  Created {len(equipment_list)} equipment items')
        return equipment_list

    def create_business_info(self):
        business, _ = BusinessInfo.objects.get_or_create(
            name='TechCorp Solutions',
            defaults={
                'description': 'Leading IT asset management solutions provider with cutting-edge technology',
                'address': '123 Business Street, Tech City, TC 12345',
                'contact_email': 'info@techcorp.com',
                'contact_phone': '+1234567890',
                'website': 'https://techcorp.com',
                'primary_color': '#2563eb',
                'secondary_color': '#f8fafc',
                'is_active': True
            }
        )
        self.stdout.write('  Created business info')
        return business

    def create_social_media_links(self):
        business = BusinessInfo.objects.filter(is_active=True).first()
        if not business:
            return
            
        social_platforms = [
            ('facebook', 'https://facebook.com/techcorp'),
            ('linkedin', 'https://linkedin.com/company/techcorp'),
            ('twitter', 'https://twitter.com/techcorp'),
            ('youtube', 'https://youtube.com/techcorp'),
            ('instagram', 'https://instagram.com/techcorp'),
            ('github', 'https://github.com/techcorp'),
        ]
        count = 0
        for platform, url in social_platforms:
            SocialMediaLink.objects.get_or_create(
                business=business,
                platform=platform,
                defaults={'url': url}
            )
            count += 1
        self.stdout.write(f'  Created {count} social media links')

    def create_notification_templates(self):
        templates = [
            ('REQUEST_CREATED', 'New IT Request - #{{request_id}}', 'A new {{request_type}} request has been submitted by {{user_name}}. Please review and approve.'),
            ('REQUEST_APPROVED', 'Request Approved - #{{request_id}}', 'Your {{request_type}} request has been approved by {{manager_name}} and is now being processed by IT.'),
            ('REQUEST_REJECTED', 'Request Rejected - #{{request_id}}', 'Your {{request_type}} request has been rejected. Please contact your manager for more details.'),
            ('REQUEST_COMPLETED', 'Request Completed - #{{request_id}}', 'Your {{request_type}} request has been completed. Please collect your equipment from IT department.'),
            ('EQUIPMENT_ASSIGNED', 'New Equipment Assigned', 'New equipment ({{equipment_name}}) has been assigned to you. Serial: {{serial_number}}'),
            ('EQUIPMENT_RETURNED', 'Equipment Returned', 'Equipment ({{equipment_name}}) has been returned and is now available in inventory.'),
            ('MAINTENANCE_DUE', 'Maintenance Due', 'Equipment {{equipment_name}} (SN: {{serial_number}}) requires maintenance.'),
            ('WARRANTY_EXPIRING', 'Warranty Expiring', 'Equipment {{equipment_name}} warranty expires on {{expiry_date}}. Please plan for renewal.'),
            ('SYSTEM_ALERT', 'System Alert', 'Important: {{alert_message}}'),
        ]
        count = 0
        for notif_type, subject, message in templates:
            NotificationTemplate.objects.get_or_create(
                notification_type=notif_type,
                defaults={
                    'subject_template': subject,
                    'message_template': message,
                    'is_active': True
                }
            )
            count += 1
        self.stdout.write(f'  Created {count} notification templates')

    def create_requests(self, employees, categories, brands, vendors, equipment_list, it_admin):
        requests_data = [
            (employees[0], 'NEW', 'HIGH', categories['Laptop'], brands['Dell'], 'Need a high-performance laptop for new project', 'PENDING', None),
            (employees[1], 'NEW', 'MEDIUM', categories['Laptop'], brands['Apple'], 'Current laptop is running slow', 'MANAGER_APPROVED', None),
            (employees[2], 'NEW', 'LOW', categories['Monitor'], brands['Samsung'], 'Need second monitor for dual display', 'PENDING', None),
            (employees[3], 'REPAIR', 'HIGH', None, None, 'Laptop not powering on', 'IT_RECEIVED', equipment_list[18]),
            (employees[4], 'NEW', 'MEDIUM', categories['Headphones'], brands['Sony'], 'Need noise-cancelling headphones for open office', 'PENDING', None),
            (employees[5], 'NEW', 'HIGH', categories['Tablet'], brands['Apple'], 'Need tablet for client presentations', 'MANAGER_APPROVED', None),
            (employees[6], 'REPAIR', 'MEDIUM', None, None, 'Phone screen cracked', 'IN_PROGRESS', equipment_list[41], vendors['Repair Masters']),
            (employees[7], 'NEW', 'LOW', categories['Webcam'], brands['Logitech'], 'Need better webcam for video calls', 'PENDING', None),
            (employees[8], 'NEW', 'MEDIUM', categories['Keyboard'], brands['Logitech'], 'Current keyboard keys not working', 'PENDING', None),
            (employees[9], 'REPAIR', 'MEDIUM', None, None, 'Printer paper jam issues', 'PENDING', equipment_list[19]),
        ]

        requests_list = []
        for data in requests_data:
            user, req_type, priority = data[0], data[1], data[2]
            category = data[3]
            brand = data[4]
            reason, status = data[5], data[6]
            equipment = data[7] if len(data) > 7 and data[7] else None
            vendor = data[8] if len(data) > 8 and data[8] else None

            cat_needed = category if req_type == 'NEW' else None
            brand_pref = brand if req_type == 'NEW' else None

            req = Request.objects.create(
                user=user,
                request_type=req_type,
                priority=priority,
                reason=reason,
                category_needed=cat_needed,
                brand_preference=brand_pref,
                equipment=equipment,
                status=status,
                assigned_vendor=vendor,
            )
            requests_list.append(req)

            if status != 'PENDING':
                manager = user.manager if user.manager else it_admin
                RequestLog.objects.create(
                    request=req,
                    action_by=manager,
                    old_status='PENDING',
                    new_status=status,
                    remarks=f'Request updated to {status}'
                )

        self.stdout.write(f'  Created {len(requests_list)} requests')
        return requests_list

    def create_assignments(self, equipment_list, employees, it_admin):
        count = 0
        for eq in equipment_list:
            if eq.status == 'ASSIGNED' and eq.assigned_to:
                assignment, created = Assignment.objects.get_or_create(
                    equipment=eq,
                    user=eq.assigned_to,
                    defaults={
                        'assigned_by': it_admin,
                        'notes': f'Assigned for {eq.assigned_to.department.name} department duties'
                    }
                )
                if created:
                    count += 1
        self.stdout.write(f'  Created {count} assignments')
        return count

    def create_equipment_logs(self, equipment_list, it_admin):
        status_changes = [
            (equipment_list[0], 'AVAILABLE', 'ASSIGNED', 'Initial assignment'),
            (equipment_list[3], 'AVAILABLE', 'ASSIGNED', 'Assigned to employee'),
            (equipment_list[18], 'AVAILABLE', 'REPAIRING', 'Sent for repair'),
            (equipment_list[19], 'AVAILABLE', 'REPAIRING', 'Sent for repair'),
        ]
        count = 0
        for eq, old_status, new_status, remarks in status_changes:
            EquipmentLog.objects.create(
                equipment=eq,
                action_by=it_admin,
                old_status=old_status,
                new_status=new_status,
                remarks=remarks
            )
            count += 1
        self.stdout.write(f'  Created {count} equipment logs')
        return count

    def create_notifications(self, employees, it_admin, requests_list):
        notif_data = [
            (employees[0], 'REQUEST_CREATED', 'Request Submitted', f'Your request has been submitted and is awaiting manager approval.', 'MEDIUM'),
            (employees[1], 'REQUEST_APPROVED', 'Request Approved', 'Your request has been approved!', 'HIGH'),
            (employees[2], 'EQUIPMENT_ASSIGNED', 'New Equipment', 'You have been assigned new equipment.', 'HIGH'),
            (employees[3], 'MAINTENANCE_DUE', 'Maintenance Required', 'Your equipment requires maintenance attention.', 'MEDIUM'),
            (employees[4], 'REQUEST_CREATED', 'Request Received', 'Your request has been received by IT department.', 'LOW'),
            (it_admin, 'SYSTEM_ALERT', 'New System Alert', 'System check completed successfully.', 'LOW'),
            (it_admin, 'WARRANTY_EXPIRING', 'Warranty Alert', '5 equipment items have warranties expiring soon.', 'HIGH'),
        ]
        
        count = 0
        for user, notif_type, title, message, priority in notif_data:
            Notification.objects.create(
                recipient=user,
                notification_type=notif_type,
                title=title,
                message=message,
                priority=priority,
                related_request=requests_list[0] if requests_list and count < 4 else None
            )
            count += 1
        self.stdout.write(f'  Created {count} notifications')
        return count

    def regenerate_qr_codes(self):
        self.stdout.write('Regenerating QR codes...')
        for eq in Equipment.objects.all():
            if eq.qr_code:
                eq.qr_code.delete(save=True)
            eq.save()
        self.stdout.write(f'  Regenerated QR codes for {Equipment.objects.count()} equipment')

    def print_summary(self, equipment_list, employees, requests_list):
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Data population complete!'))
        self.stdout.write('')
        self.stdout.write('Summary:')
        self.stdout.write(f'  - Users: {User.objects.count()}')
        self.stdout.write(f'  - Equipment: {Equipment.objects.count()}')
        self.stdout.write(f'  - Requests: {Request.objects.count()}')
        self.stdout.write(f'  - Assignments: {Assignment.objects.count()}')
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  IT Admin: admin / admin123')
        self.stdout.write('  Manager:  manager_hr / manager123 (or manager_finance / manager123)')
        self.stdout.write('  Employee: alice / employee123 (or any employee / employee123)')
