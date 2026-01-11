import os
import django

# Use production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hunarmitra.settings.prod')
django.setup()

from apps.users.models import User

# Create superuser if it doesn't exist
if not User.objects.filter(phone='+919999999999').exists():
    User.objects.create_superuser(
        phone='+919999999999',
        password='HunarMitra@2026',
        first_name='Admin',
        last_name='User'
    )
    print("✅ Superuser created successfully!")
    print("Phone: +919999999999")
    print("Password: HunarMitra@2026")
else:
    print("ℹ️  Superuser already exists")
