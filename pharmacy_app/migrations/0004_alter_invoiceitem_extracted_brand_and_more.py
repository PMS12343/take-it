# Generated by Django 5.1.7 on 2025-03-28 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy_app', '0003_supplier_invoiceupload_invoiceitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='extracted_brand',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='extracted_name',
            field=models.CharField(max_length=500),
        ),
    ]
