from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    """Profile model extending the built-in User model"""
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Pharmacist', 'Pharmacist'),
        ('Sales Clerk', 'Sales Clerk'),
        ('Manager', 'Manager'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class DrugCategory(models.Model):
    """Model for drug categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Drug Categories"
    
    def __str__(self):
        return self.name

class Drug(models.Model):
    """Model for drug information and inventory"""
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text="Product barcode (optional)")
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(DrugCategory, on_delete=models.SET_NULL, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reorder_level = models.PositiveIntegerField(default=10)
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name', 'brand']
    
    def __str__(self):
        return f"{self.name} ({self.brand})"
    
    def is_low_stock(self):
        """Check if drug stock is below reorder level"""
        return self.stock_quantity <= self.reorder_level
    
    def is_expiring_soon(self):
        """Check if drug is expiring within 2 months"""
        today = timezone.now().date()
        days_until_expiry = (self.expiry_date - today).days
        return 0 < days_until_expiry <= 60
    
    def is_expired(self):
        """Check if drug is already expired"""
        return self.expiry_date < timezone.now().date()

class Patient(models.Model):
    """Model for patient information"""
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('Unknown', 'Unknown'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='Unknown')
    disease_history = models.TextField(blank=True, null=True)
    medication_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Sale(models.Model):
    """Model for recording sales transactions"""
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, default='Cash')
    payment_status = models.CharField(max_length=50, default='Paid')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.patient}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate a unique invoice number"""
        # Format: INV-YYYYMMDD-XXXX
        today = timezone.now().strftime('%Y%m%d')
        random_suffix = str(uuid.uuid4().int)[:4]
        return f"INV-{today}-{random_suffix}"
    
    @property
    def item_count(self):
        return self.saleitems.count()

class SaleItem(models.Model):
    """Model for individual items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='saleitems')
    drug = models.ForeignKey(Drug, on_delete=models.SET_NULL, null=True)
    drug_name = models.CharField(max_length=200)  # Store name at time of sale
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Unit price at time of sale
    
    def __str__(self):
        return f"{self.drug_name} x {self.quantity} (Invoice #{self.sale.invoice_number})"
    
    @property
    def total_price(self):
        return self.quantity * self.price

class InventoryLog(models.Model):
    """Model for tracking inventory changes"""
    OPERATION_CHOICES = [
        ('ADD', 'Stock Added'),
        ('REMOVE', 'Stock Removed'),
        ('ADJUST', 'Stock Adjusted'),
        ('SALE', 'Sale Transaction'),
        ('RETURN', 'Return to Inventory'),
    ]
    
    drug = models.ForeignKey(Drug, on_delete=models.SET_NULL, null=True)
    quantity_change = models.IntegerField()  # Can be positive (increase) or negative (decrease)
    operation_type = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True)  # e.g., sale invoice or order number
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        action = "added to" if self.quantity_change > 0 else "removed from"
        return f"{abs(self.quantity_change)} units {action} {self.drug} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class DrugInteraction(models.Model):
    """Model for drug-drug interactions"""
    SEVERITY_CHOICES = [
        ('SEVERE', 'Severe - Avoid Combination'),
        ('MODERATE', 'Moderate - Use with Caution'),
        ('MILD', 'Mild - Monitor Patient'),
        ('NONE', 'No Interaction'),
    ]
    
    drug_one = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_one')
    drug_two = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_two')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    
    class Meta:
        unique_together = ('drug_one', 'drug_two')
    
    def __str__(self):
        return f"Interaction between {self.drug_one} and {self.drug_two}: {self.severity}"


class Supplier(models.Model):
    """Model for drug suppliers/vendors"""
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class InvoiceUpload(models.Model):
    """Model for storing uploaded supplier invoices"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Processing'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIALLY_PROCESSED', 'Partially Processed'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('PDF', 'PDF Document'),
        ('IMAGE', 'Image'),
        ('EXCEL', 'Excel Spreadsheet'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_date = models.DateField(blank=True, null=True)
    file = models.FileField(upload_to='invoice_uploads/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    processing_notes = models.TextField(blank=True, null=True)
    total_items_found = models.IntegerField(default=0)
    total_items_matched = models.IntegerField(default=0)
    output_file = models.FileField(upload_to='invoice_outputs/', blank=True, null=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number or 'Unknown'} - {self.supplier.name if self.supplier else 'Unknown'}"
    
    
class InvoiceItem(models.Model):
    """Model for individual items extracted from uploaded invoices"""
    MATCH_STATUS_CHOICES = [
        ('MATCHED', 'Matched to Drug'),
        ('PARTIAL_MATCH', 'Partially Matched'),
        ('UNMATCHED', 'No Match Found'),
        ('MANUALLY_MATCHED', 'Manually Matched'),
        ('IGNORED', 'Ignored'),
    ]
    
    invoice = models.ForeignKey(InvoiceUpload, on_delete=models.CASCADE, related_name='items')
    extracted_name = models.CharField(max_length=200)
    extracted_brand = models.CharField(max_length=200, blank=True, null=True)
    extracted_quantity = models.CharField(max_length=50, blank=True, null=True)
    extracted_cost_price = models.CharField(max_length=50, blank=True, null=True)
    extracted_batch_number = models.CharField(max_length=100, blank=True, null=True)
    extracted_expiry_date = models.CharField(max_length=50, blank=True, null=True)
    
    quantity = models.PositiveIntegerField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    match_status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='UNMATCHED')
    matched_drug = models.ForeignKey(Drug, on_delete=models.SET_NULL, null=True, blank=True)
    match_confidence = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    processing_notes = models.TextField(blank=True, null=True)
    is_imported = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.extracted_name} ({self.get_match_status_display()})"
