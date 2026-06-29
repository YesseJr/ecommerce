"""
Management command to populate Élan Parfums CRM with sample data.
Usage: python manage.py seed
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample perfume business data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('🌱  Seeding Élan Parfums CRM...'))
        self._create_users()
        self._create_fragrances()
        self._create_contacts()
        self._create_companies()
        self._create_leads()
        self._create_deals()
        self._create_expenses()
        self.stdout.write(self.style.SUCCESS('✅  Seed complete! Login: admin / admin123'))

    def _create_users(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin', password='admin123',
                first_name='Admin', last_name='User',
                email='admin@elanparfums.co.tz', role='admin'
            )
        if not User.objects.filter(username='manager').exists():
            u = User(username='manager', first_name='Zawadi', last_name='Kimani',
                     email='zawadi@elanparfums.co.tz', role='manager')
            u.set_password('manager123')
            u.save()
        if not User.objects.filter(username='cashier').exists():
            u = User(username='cashier', first_name='James', last_name='Mwangi',
                     email='cashier@elanparfums.co.tz', role='cashier')
            u.set_password('cashier123')
            u.save()
        self.stdout.write('  ✓ Users')

    def _create_fragrances(self):
        from apps.inventory.models import Fragrance
        fragrances_data = [
            ('Rose Oud',         'Al Haramain', 'ELN-001', 'edp',    '50ml',  89000, 38000, 24, 10),
            ('Amber Noir',       'Élan House',  'ELN-002', 'edp',    '100ml', 125000, 52000, 18, 8),
            ('Ocean Breeze',     'Élan House',  'ELN-003', 'edt',    '50ml',  65000, 28000, 32, 10),
            ('Saffron Royale',   'Swiss Arabian','ELN-004','parfum','30ml',  195000, 90000, 9,  5),
            ('Musk Tahara',      'Al Rehab',    'ELN-005', 'edc',    '100ml', 45000, 18000, 47, 15),
            ('Black Oud',        'Élan House',  'ELN-006', 'edp',    '75ml',  145000, 65000, 6,  8),
            ('Jasmine Dream',    'Lattafa',     'ELN-007', 'edp',    '50ml',  78000, 32000, 21, 10),
            ('Cedar & Smoke',    'Élan House',  'ELN-008', 'edt',    '100ml', 95000, 42000, 14, 8),
            ('Persian Rose',     'Al Haramain', 'ELN-009', 'parfum','50ml',  165000, 78000, 3,  5),
            ('Vanilla Suede',    'Lattafa',     'ELN-010', 'edp',    '100ml', 110000, 48000, 28, 10),
            ('Blue Aqua',        'Élan House',  'ELN-011', 'edt',    '100ml', 72000, 30000, 35, 12),
            ('Oud Malaki',       'Swiss Arabian','ELN-012','parfum','30ml',  210000, 98000, 7,  5),
        ]
        for name,brand,sku,conc,size,price,cost,stock,reorder in fragrances_data:
            Fragrance.objects.get_or_create(
                sku=sku,
                defaults=dict(name=name,brand=brand,concentration=conc,
                              bottle_size=size,price=Decimal(price),
                              cost_price=Decimal(cost),stock_quantity=stock,
                              reorder_level=reorder,is_active=True)
            )
        self.stdout.write('  ✓ Fragrances (12)')

    def _create_contacts(self):
        from apps.contacts.models import Contact
        admin = User.objects.filter(username='admin').first()
        contacts_data = [
            ('Zawadi',  'Kimani', 'zawadi@email.com',  '0712098321', 'Dar es Salaam', 67, 'vip'),
            ('Fatuma',  'Said',   'fatuma@email.com',  '0687234009', 'Arusha',         48, 'vip'),
            ('Amina',   'Rashid', 'amina@email.com',   '0712345001', 'Dar es Salaam', 34, 'active'),
            ('David',   'Njoroge','david@email.com',   '0756778900', 'Dodoma',         29, 'active'),
            ('James',   'Mwangi', 'james@email.com',   '0756123004', 'Dar es Salaam', 21, 'active'),
            ('Brian',   'Osei',   'brian@email.com',   '0745890012', 'Mwanza',         12, 'new'),
            ('Halima',  'Musa',   'halima@email.com',  '0712567890', 'Arusha',         8,  'new'),
            ('Neema',   'Ochieng','neema@email.com',   '0765432109', 'Nairobi',        5,  'new'),
            ('Salma',   'Hassan', 'salma@email.com',   '0711223344', 'Dar es Salaam', 18, 'active'),
            ('Rehema',  'Juma',   'rehema@email.com',  '0699887766', 'Zanzibar',       31, 'active'),
        ]
        for fn,ln,email,phone,city,pts,status in contacts_data:
            Contact.objects.get_or_create(
                phone=phone,
                defaults=dict(first_name=fn,last_name=ln,email=email,
                              city=city,loyalty_points=pts,status=status,
                              created_by=admin)
            )
        self.stdout.write('  ✓ Contacts (10)')

    def _create_companies(self):
        from apps.companies.models import Company
        companies_data = [
            ('Zanzibar Luxury Spa',  'spa',       '0242010101', 'info@zlspa.co.tz',   'Zanzibar'),
            ('Serena Hotel Dar',     'hotel',     '0222119000', 'info@serena.co.tz',  'Dar es Salaam'),
            ('ABC Events Ltd',       'events',    '0755123000', 'abc@events.co.tz',   'Dar es Salaam'),
            ('Fragrance Hub Store',  'retailer',  '0713445566', 'hub@frag.co.tz',     'Arusha'),
            ('GreenLeaf Wellness',   'spa',       '0687321654', 'info@greenleaf.co',  'Mwanza'),
        ]
        for name,t,phone,email,city in companies_data:
            Company.objects.get_or_create(name=name, defaults=dict(type=t,phone=phone,email=email,city=city))
        self.stdout.write('  ✓ Companies (5)')

    def _create_leads(self):
        from apps.leads.models import Lead
        from apps.contacts.models import Contact
        admin = User.objects.filter(username='admin').first()
        lead_data = [
            ('Baraka Ndosi', 'baraka@email.com', '0756001122', 'walk_in',  'new'),
            ('Grace Otieno', 'grace@email.com',  '0713445678', 'referral', 'contacted'),
            ('Hassan Ali',   'hassan@email.com', '0699001234', 'social',   'qualified'),
        ]
        for name,email,phone,source,status in lead_data:
            Lead.objects.get_or_create(
                phone=phone,
                defaults=dict(name=name,email=email,source=source,
                              status=status,created_by=admin,assigned_to=admin)
            )
        self.stdout.write('  ✓ Leads (3)')

    def _create_deals(self):
        from apps.deals.models import Deal
        from apps.contacts.models import Contact
        from apps.companies.models import Company
        admin = User.objects.filter(username='admin').first()
        contacts = {c.full_name: c for c in Contact.objects.all()}
        companies = {co.name: co for co in Company.objects.all()}
        deals_data = [
            ('Bulk fragrance order — Zanzibar Spa',  companies.get('Zanzibar Luxury Spa'),  None,                         Decimal('1200000'), 'proposal',    'email'),
            ('Wedding favors — Rehema Juma',         None, contacts.get('Rehema Juma'),      Decimal('320000'),  'qualified',   'referral'),
            ('Corporate gift set — Serena Hotel',    companies.get('Serena Hotel Dar'),      None,                         Decimal('850000'),  'negotiation', 'email'),
            ('VIP package — Zawadi Kimani',          None, contacts.get('Zawadi Kimani'),     Decimal('670000'),  'won',         'walk_in'),
            ('Monthly restock — Fragrance Hub',      companies.get('Fragrance Hub Store'),   None,                         Decimal('480000'),  'won',         'referral'),
            ('Spa amenities — GreenLeaf',            companies.get('GreenLeaf Wellness'),    None,                         Decimal('395000'),  'lead',        'online'),
            ('Personal collection — Amina Rashid',  None, contacts.get('Amina Rashid'),      Decimal('145000'),  'qualified',   'walk_in'),
        ]
        for title,company,contact,value,stage,source in deals_data:
            Deal.objects.get_or_create(
                title=title,
                defaults=dict(company=company,contact=contact,value=value,
                              stage=stage,source=source,assigned_to=admin)
            )
        self.stdout.write('  ✓ Deals (7)')

    def _create_expenses(self):
        from apps.expenses.models import Expense
        from datetime import date
        admin = User.objects.filter(username='admin').first()
        today = date.today()
        expenses_data = [
            ('Monthly rent',             'rent',       800000, 'bank',  today.replace(day=1)),
            ('Electricity & water',      'utilities',   85000, 'mpesa', today.replace(day=5)),
            ('Display bottles & testers','supplies',    45000, 'cash',  today.replace(day=8)),
            ('Staff salaries — May',     'salaries',  1200000,'bank',  today.replace(day=28)),
            ('Instagram ads',            'marketing',   60000, 'card',  today.replace(day=10)),
            ('Packaging & gift wrap',    'supplies',    32000, 'cash',  today.replace(day=14)),
        ]
        for title,cat,amount,pay,d in expenses_data:
            Expense.objects.get_or_create(
                title=title,
                defaults=dict(category=cat,amount=Decimal(amount),
                              payment_method=pay,date=d,recorded_by=admin)
            )
        self.stdout.write('  ✓ Expenses (6)')
