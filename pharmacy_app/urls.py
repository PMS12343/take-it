from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Dashboard
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Drugs
    path('drugs/', views.drug_list, name='drug_list'),
    path('drugs/create/', views.drug_create, name='drug_create'),
    path('drugs/<int:pk>/', views.drug_detail, name='drug_detail'),
    path('drugs/<int:pk>/edit/', views.drug_edit, name='drug_edit'),
    path('drugs/<int:pk>/delete/', views.drug_delete, name='drug_delete'),
    
    # Patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    
    # Sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/create/', views.sale_create, name='sale_create'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    
    # Invoices
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    
    # Reports
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/sales/export/pdf/', views.sales_report_pdf, name='sales_report_pdf'),
    path('reports/sales/export/excel/', views.sales_report_excel, name='sales_report_excel'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    
    # Drug Interactions
    path('interactions/', views.interaction_list, name='interaction_list'),
    path('interactions/create/', views.interaction_create, name='interaction_create'),
    path('interactions/<int:pk>/edit/', views.interaction_edit, name='interaction_edit'),
    path('interactions/<int:pk>/delete/', views.interaction_delete, name='interaction_delete'),
]
