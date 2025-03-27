from django.contrib import admin
from .models import (
    Drug, DrugCategory, Patient, Sale, SaleItem, InventoryLog, 
    DrugInteraction, UserProfile, Supplier, InvoiceUpload, InvoiceItem
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(DrugCategory)
class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'stock_quantity', 'selling_price', 'expiry_date', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'brand')
    readonly_fields = ('created_at', 'updated_at')
    
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'age', 'sex', 'blood_type', 'phone_number', 'created_at')
    list_filter = ('sex', 'blood_type')
    search_fields = ('first_name', 'last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'patient', 'user', 'total_amount', 'date')
    list_filter = ('date', 'user')
    search_fields = ('invoice_number', 'patient__first_name', 'patient__last_name')
    readonly_fields = ('created_at',)
    
@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'drug', 'quantity', 'price')
    list_filter = ('sale__date',)
    search_fields = ('sale__invoice_number', 'drug__name')
    
@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('drug', 'quantity_change', 'operation_type', 'user', 'timestamp')
    list_filter = ('operation_type', 'timestamp')
    search_fields = ('drug__name', 'user__username')
    readonly_fields = ('timestamp',)

@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    list_display = ('drug_one', 'drug_two', 'severity', 'description')
    list_filter = ('severity',)
    search_fields = ('drug_one__name', 'drug_two__name', 'description')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ('extracted_name', 'extracted_brand', 'extracted_quantity', 'extracted_cost_price', 
              'match_status', 'matched_drug', 'match_confidence')
    readonly_fields = ('match_confidence',)
    
@admin.register(InvoiceUpload)
class InvoiceUploadAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier', 'upload_date', 'processing_status', 
                    'total_items_found', 'total_items_matched')
    list_filter = ('processing_status', 'upload_date', 'supplier')
    search_fields = ('invoice_number', 'supplier__name')
    readonly_fields = ('upload_date', 'total_items_found', 'total_items_matched', 'processing_status')
    inlines = [InvoiceItemInline]
    
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('extracted_name', 'extracted_brand', 'extracted_quantity', 'extracted_cost_price', 
                    'match_status', 'matched_drug', 'match_confidence')
    list_filter = ('match_status', 'invoice__supplier')
    search_fields = ('extracted_name', 'extracted_brand', 'matched_drug__name')
    readonly_fields = ('match_confidence',)
