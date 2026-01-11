import os
import django
from django.utils import timezone
from datetime import timedelta

# No setup needed inside shell

from apps.users.models import User
from apps.services.models import Service
from apps.jobs.models import Job

print("Creating Dummy Data (v2)...")

# 1. Create Employer User
# Note: User model uses 'phone' as identifier
employer, _ = User.objects.get_or_create(
    phone='9999999999', 
    defaults={
        'first_name': 'Ramesh',
        'last_name': 'Contractor',
        'is_active': True,
        'role': 'contractor'
    }
)
if not employer.has_usable_password():
    employer.set_password('password')
    employer.save()
print(f"Created/Found Employer: {employer.first_name} {employer.last_name}")

# 2. Create Services
services_data = [
    {'name': 'Carpenter', 'title_en': 'Carpenter', 'title_hi': 'Badhai (बढ़ई)', 'category': 'Repair'},
    {'name': 'Painter', 'title_en': 'Painter', 'title_hi': 'Putai Wala (पुताई वाला)', 'category': 'Repair'},
    {'name': 'Electrician', 'title_en': 'Electrician', 'title_hi': 'Bijli Wala (बिजली वाला)', 'category': 'Urgent'},
    {'name': 'Plumber', 'title_en': 'Plumber', 'title_hi': 'Nal Mistri (नल मिस्त्री)', 'category': 'Repair'},
]

services = {}
for svc in services_data:
    obj, _ = Service.objects.get_or_create(
        name=svc['name'],
        defaults={
            'title_en': svc['title_en'],
            'title_hi': svc['title_hi'],
            'category': svc['category'],
            'description': f"Professional {svc['name']} services",
            'is_active': True
        }
    )
    services[svc['name']] = obj
print(f"Created Services: {list(services.keys())}")

# 3. Create Dummy Jobs
jobs_config = [
    {
        'title': 'Wooden Door Repair',
        'service': 'Carpenter',
        'desc': 'Front door hinge is broken and needs fixing',
        'loc': 'Gomti Nagar, Lucknow',
        'lat': 26.8467,
        'lng': 80.9462,
        'budget': 500.0,
        'days': 1
    },
    {
        'title': '3BHK Flat Painting',
        'service': 'Painter',
        'desc': 'Need full painting for 3BHK flat. Material provided.',
        'loc': 'Indira Nagar, Lucknow',
        'lat': 26.8867,
        'lng': 80.9962,
        'budget': 15000.0,
        'days': 3
    },
    {
        'title': 'Switch Board Installation',
        'service': 'Electrician',
        'desc': 'Install 4 new switch boards in office.',
        'loc': 'Hazratganj, Lucknow',
        'lat': 26.8467,
        'lng': 80.9462,
        'budget': 1200.0,
        'days': 0
    },
    {
        'title': 'Bathroom Pipe Leakage',
        'service': 'Plumber',
        'desc': 'Available immediately. Water leaking from main pipe.',
        'loc': 'Alambagh, Lucknow',
        'lat': 26.8067,
        'lng': 80.9062,
        'budget': 800.0,
        'days': 1
    }
]

for job in jobs_config:
    j, created = Job.objects.get_or_create(
        title=job['title'],
        defaults={
            'poster': employer,
            'service': services[job['service']],
            'description': job['desc'],
            'status': 'open',
            'location': job['loc'],
            'latitude': job['lat'],
            'longitude': job['lng'],
            'budget': job['budget'],
            'scheduled_date': timezone.now() + timedelta(days=job['days'])
        }
    )
    if created:
        print(f"Created Job: {job['title']}")
    else:
        print(f"Job exists: {job['title']}")

print("Dummy data population complete!")
