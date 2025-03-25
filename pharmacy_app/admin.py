from django.contrib import admin
from .models import Drug, Patient, Sale, SaleItem, InventoryLog, DrugInteraction

@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'quantity', 'selling_price', 'expiry_date', 'is_low_stock')
    list_filter = ('brand', 'is_low_stock')
    search_fields = ('name', 'brand')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'sex', 'blood_type')
    list_filter = ('sex', 'blood_type')
    search_fields = ('name',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'created_by', 'date', 'total_amount')
    list_filter = ('date', 'created_by')
    search_fields = ('patient__name',)

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'drug', 'quantity', 'price_each')
    list_filter = ('drug',)

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('drug', 'change_quantity', 'reason', 'changed_by', 'timestamp')
    list_filter = ('drug', 'timestamp', 'changed_by')

@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    list_display = ('drug1', 'drug2', 'severity')
    list_filter = ('severity',)
    search_fields = ('drug1__name', 'drug2__name', 'description')
