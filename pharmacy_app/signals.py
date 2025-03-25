from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.utils import timezone
from .models import UserProfile, Sale, SaleItem, InventoryLog, Drug

@receiver(post_save, sender=UserProfile)
def assign_group_based_on_role(sender, instance, created, **kwargs):
    """
    Assign Django group based on user role when a UserProfile is created or updated
    """
    if instance.role:
        # Get or create the group with the role name
        group, _ = Group.objects.get_or_create(name=instance.role)
        
        # Add user to the appropriate group
        instance.user.groups.clear()
        instance.user.groups.add(group)

@receiver(post_save, sender=SaleItem)
def update_inventory_on_sale(sender, instance, created, **kwargs):
    """
    Update inventory when a sale item is created
    """
    if created and instance.drug:
        # Reduce drug stock
        drug = instance.drug
        drug.stock_quantity = max(0, drug.stock_quantity - instance.quantity)
        drug.save()
        
        # Log inventory change
        InventoryLog.objects.create(
            drug=drug,
            quantity_change=-instance.quantity,
            operation_type='SALE',
            reference=f"Invoice #{instance.sale.invoice_number}",
            user=instance.sale.user
        )

@receiver(post_delete, sender=SaleItem)
def restore_inventory_on_sale_item_delete(sender, instance, **kwargs):
    """
    Restore inventory when a sale item is deleted
    """
    if instance.drug:
        # Add back to drug stock
        drug = instance.drug
        drug.stock_quantity += instance.quantity
        drug.save()
        
        # Log inventory change
        InventoryLog.objects.create(
            drug=drug,
            quantity_change=instance.quantity,
            operation_type='RETURN',
            reference=f"Deleted from Invoice #{instance.sale.invoice_number}",
            notes="Automatic return due to deleted sale item",
            user=instance.sale.user if instance.sale.user else None
        )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create UserProfile when a new User is created
    """
    if created:
        # Default to Sales Clerk role
        UserProfile.objects.create(user=instance, role='Sales Clerk')
