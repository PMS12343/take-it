from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Drug(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def is_expiring_soon(self):
        return self.expiry_date <= (timezone.now().date() + timedelta(days=60))

    def __str__(self):
        return f"{self.name} ({self.brand})"

    class Meta:
        ordering = ['name']


class Patient(models.Model):
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)
    disease_history = models.TextField(blank=True, null=True)
    medication_history = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Sale(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='sales')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales')
    date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Sale {self.id} - {self.patient.name}"
    
    class Meta:
        ordering = ['-date']


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField()
    price_each = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Set the price from the drug's current selling price if not set
        if not self.price_each:
            self.price_each = self.drug.selling_price
        
        # Create the sale item
        super().save(*args, **kwargs)
        
        # Update sale total
        self.sale.total_amount = sum(item.price_each * item.quantity for item in self.sale.items.all())
        self.sale.save()
        
        # Create inventory log entry
        InventoryLog.objects.create(
            drug=self.drug,
            change_quantity=-self.quantity,
            reason=f"Sale {self.sale.id}",
            changed_by=self.sale.created_by
        )
        
        # Update drug quantity
        self.drug.quantity -= self.quantity
        self.drug.save()
    
    def __str__(self):
        return f"{self.sale} - {self.drug.name} x{self.quantity}"


class InventoryLog(models.Model):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='inventory_logs')
    change_quantity = models.IntegerField()  # Can be positive (stocking) or negative (sales, expiry)
    reason = models.CharField(max_length=200)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='inventory_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.drug.name} - {self.change_quantity} - {self.reason}"
    
    class Meta:
        ordering = ['-timestamp']


class DrugInteraction(models.Model):
    SEVERITY_CHOICES = (
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    )
    
    drug1 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug1')
    drug2 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug2')
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    
    def __str__(self):
        return f"Interaction between {self.drug1.name} and {self.drug2.name}"
    
    class Meta:
        unique_together = ('drug1', 'drug2')
