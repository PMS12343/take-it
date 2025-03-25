"""
URL configuration for pharmacy_management project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pharmacy_app.urls')),
]
