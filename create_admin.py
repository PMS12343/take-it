from django.contrib.auth.models import User
from pharmacy_app.models import UserProfile
import django.db.utils

try:
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
    UserProfile.objects.create(user=user, role='Admin')
    print('Admin user created successfully.')
except django.db.utils.IntegrityError:
    print('Admin user already exists.')