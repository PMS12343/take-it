from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Dashboard
    path('', views.dashboard, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Drug Management
    path('drugs/', views.drug_list, name='drug_list'),
    path('drugs/add/', views.drug_add, name='drug_add'),
    path('drugs/<int:drug_id>/', views.drug_detail, name='drug_detail'),
    path('drugs/<int:drug_id>/edit/', views.drug_edit, name='drug_edit'),
    
    # Patient Management
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_add, name='patient_add'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/edit/', views.patient_edit, name='patient_edit'),
    
    # Sales
    path('sales/new/', views.new_sale, name='new_sale'),
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:sale_id>/edit/', views.sale_edit, name='sale_edit'),
    path('sales/<int:sale_id>/delete/', views.sale_delete, name='sale_delete'),
    path('sales/<int:sale_id>/invoice/', views.sale_invoice, name='sale_invoice'),
    
    # Reports
    path('reports/', views.reports_index, name='reports_index'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    
    # API endpoints
    path('api/drugs/<int:drug_id>/info/', views.get_drug_info, name='get_drug_info'),
    path('api/drugs/barcode/', views.get_drug_by_barcode, name='get_drug_by_barcode'),
]
