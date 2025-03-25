
from django.contrib.auth.models import User
from pharmacy_app.models import UserProfile
import django.db.utils

try:
    # Delete existing admin user if exists
    User.objects.filter(username='pharmacy_admin').delete()
    
    # Create new admin user
    user = User.objects.create_superuser('pharmacy_admin', 'admin@pharmacy.com', 'pharmacy123')
    UserProfile.objects.create(user=user, role='Admin')
    print('Admin user created successfully.')
except django.db.utils.IntegrityError:
    print('Admin user already exists.')
