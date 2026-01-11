import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hunarmitra.settings.dev')
django.setup()

from apps.users.models import User

if not User.objects.filter(phone='+919999999999').exists():
    User.objects.create_superuser(
        phone='+919999999999',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("✅ Superuser created: +919999999999 / admin123")
else:
    print("Superuser already exists")
