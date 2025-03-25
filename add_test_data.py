import os
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy_management.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from pharmacy_app.models import (
    DrugCategory, Drug, Patient, Sale, SaleItem, 
    UserProfile, DrugInteraction
)

def create_drug_categories():
    categories = [
        {"name": "Antibiotics", "description": "Medicines that inhibit the growth of or destroy microorganisms"},
        {"name": "Analgesics", "description": "Pain relievers"},
        {"name": "Antihypertensives", "description": "Medicines for high blood pressure"},
        {"name": "Antihistamines", "description": "Medicines that oppose the action of histamine"},
        {"name": "Antidiabetics", "description": "Medications used to treat diabetes mellitus"},
    ]
    
    created_categories = []
    for category_data in categories:
        category, created = DrugCategory.objects.get_or_create(
            name=category_data["name"],
            defaults={"description": category_data["description"]}
        )
        created_categories.append(category)
        if created:
            print(f"Created category: {category.name}")
        else:
            print(f"Category already exists: {category.name}")
    
    return created_categories

def create_drugs(categories):
    drugs = [
        {
            "name": "Amoxicillin", 
            "brand": "AmoxiPlus", 
            "category": "Antibiotics",
            "description": "Treats bacterial infections",
            "cost_price": 5.00,
            "selling_price": 8.50,
            "stock_quantity": 200,
            "reorder_level": 30,
            "expiry_date": timezone.now().date() + timedelta(days=365),
            "batch_number": "AM2025001"
        },
        {
            "name": "Paracetamol", 
            "brand": "Panadol", 
            "category": "Analgesics",
            "description": "Pain and fever reducer",
            "cost_price": 2.00,
            "selling_price": 3.50,
            "stock_quantity": 300,
            "reorder_level": 50,
            "expiry_date": timezone.now().date() + timedelta(days=500),
            "batch_number": "PN2025001"
        },
        {
            "name": "Ibuprofen", 
            "brand": "Advil", 
            "category": "Analgesics",
            "description": "NSAID for pain, fever, and inflammation",
            "cost_price": 3.00,
            "selling_price": 5.25,
            "stock_quantity": 250,
            "reorder_level": 40,
            "expiry_date": timezone.now().date() + timedelta(days=450),
            "batch_number": "IB2025001"
        },
        {
            "name": "Lisinopril", 
            "brand": "Zestril", 
            "category": "Antihypertensives",
            "description": "ACE inhibitor for hypertension",
            "cost_price": 8.00,
            "selling_price": 14.50,
            "stock_quantity": 150,
            "reorder_level": 25,
            "expiry_date": timezone.now().date() + timedelta(days=300),
            "batch_number": "LS2025001"
        },
        {
            "name": "Cetirizine", 
            "brand": "Zyrtec", 
            "category": "Antihistamines",
            "description": "Antihistamine for allergies",
            "cost_price": 4.00,
            "selling_price": 7.25,
            "stock_quantity": 180,
            "reorder_level": 30,
            "expiry_date": timezone.now().date() + timedelta(days=400),
            "batch_number": "CZ2025001"
        },
        {
            "name": "Metformin", 
            "brand": "Glucophage", 
            "category": "Antidiabetics",
            "description": "Oral medication for type 2 diabetes",
            "cost_price": 6.00,
            "selling_price": 11.75,
            "stock_quantity": 120,
            "reorder_level": 20,
            "expiry_date": timezone.now().date() + timedelta(days=350),
            "batch_number": "MF2025001"
        },
        {
            "name": "Loratadine", 
            "brand": "Claritin", 
            "category": "Antihistamines",
            "description": "Non-drowsy antihistamine",
            "cost_price": 5.00,
            "selling_price": 9.50,
            "stock_quantity": 150,
            "reorder_level": 25,
            "expiry_date": timezone.now().date() + timedelta(days=425),
            "batch_number": "LR2025001"
        },
        {
            "name": "Ciprofloxacin", 
            "brand": "Cipro", 
            "category": "Antibiotics",
            "description": "Broad-spectrum antibiotic",
            "cost_price": 9.00,
            "selling_price": 15.75,
            "stock_quantity": 100,
            "reorder_level": 20,
            "expiry_date": timezone.now().date() + timedelta(days=275),
            "batch_number": "CP2025001"
        },
        {
            "name": "Aspirin", 
            "brand": "Bayer", 
            "category": "Analgesics",
            "description": "Pain reliever and blood thinner",
            "cost_price": 2.50,
            "selling_price": 4.75,
            "stock_quantity": 280,
            "reorder_level": 45,
            "expiry_date": timezone.now().date() + timedelta(days=475),
            "batch_number": "AS2025001"
        },
        {
            "name": "Losartan", 
            "brand": "Cozaar", 
            "category": "Antihypertensives",
            "description": "ARB for hypertension",
            "cost_price": 7.50,
            "selling_price": 13.25,
            "stock_quantity": 130,
            "reorder_level": 25,
            "expiry_date": timezone.now().date() + timedelta(days=320),
            "batch_number": "LS2025002"
        },
    ]
    
    category_map = {category.name: category for category in categories}
    created_drugs = []
    
    for drug_data in drugs:
        category_name = drug_data.pop("category")
        category = category_map.get(category_name)
        
        if category:
            drug, created = Drug.objects.get_or_create(
                name=drug_data["name"],
                brand=drug_data["brand"],
                defaults={
                    "description": drug_data["description"],
                    "category": category,
                    "cost_price": drug_data["cost_price"],
                    "selling_price": drug_data["selling_price"],
                    "stock_quantity": drug_data["stock_quantity"],
                    "reorder_level": drug_data["reorder_level"],
                    "expiry_date": drug_data["expiry_date"],
                    "batch_number": drug_data["batch_number"],
                    "is_active": True
                }
            )
            
            created_drugs.append(drug)
            if created:
                print(f"Created drug: {drug.name}")
            else:
                print(f"Drug already exists: {drug.name}")
        else:
            print(f"Category not found: {category_name}")
    
    return created_drugs

def create_drug_interactions(drugs):
    interactions = [
        {
            "drug_one_name": "Aspirin",
            "drug_two_name": "Ibuprofen",
            "severity": "MODERATE",
            "description": "May decrease the cardioprotective effects of aspirin and increase GI risk."
        },
        {
            "drug_one_name": "Lisinopril",
            "drug_two_name": "Losartan",
            "severity": "MODERATE",
            "description": "Increased risk of hypotension, hyperkalemia, and renal impairment."
        },
        {
            "drug_one_name": "Ciprofloxacin",
            "drug_two_name": "Metformin",
            "severity": "MILD",
            "description": "May enhance the hypoglycemic effect of Metformin."
        }
    ]
    
    drug_map = {drug.name: drug for drug in drugs}
    
    for interaction_data in interactions:
        drug_one = drug_map.get(interaction_data["drug_one_name"])
        drug_two = drug_map.get(interaction_data["drug_two_name"])
        
        if drug_one and drug_two:
            interaction, created = DrugInteraction.objects.get_or_create(
                drug_one=drug_one,
                drug_two=drug_two,
                defaults={
                    "severity": interaction_data["severity"],
                    "description": interaction_data["description"]
                }
            )
            
            if created:
                print(f"Created interaction: {drug_one.name} - {drug_two.name}")
            else:
                print(f"Interaction already exists: {drug_one.name} - {drug_two.name}")
        else:
            print(f"Could not create interaction: {interaction_data['drug_one_name']} - {interaction_data['drug_two_name']}")

def create_patients():
    patients = [
        {
            "first_name": "John",
            "last_name": "Doe",
            "age": 35,
            "sex": "M",
            "address": "123 Main St, Anytown, CA 12345",
            "phone_number": "555-123-4567",
            "email": "john.doe@example.com",
            "blood_type": "A+",
            "disease_history": "Hypertension, High cholesterol",
            "medication_history": "Lisinopril 10mg daily, Simvastatin 20mg daily",
            "allergies": "Penicillin"
        },
        {
            "first_name": "Jane",
            "last_name": "Smith",
            "age": 42,
            "sex": "F",
            "address": "456 Oak Ave, Sometown, NY 54321",
            "phone_number": "555-987-6543",
            "email": "jane.smith@example.com",
            "blood_type": "O-",
            "disease_history": "Type 2 diabetes, Asthma",
            "medication_history": "Metformin 500mg twice daily, Albuterol inhaler as needed",
            "allergies": "Sulfa drugs"
        },
        {
            "first_name": "Michael",
            "last_name": "Johnson",
            "age": 28,
            "sex": "M",
            "address": "789 Pine Rd, Othertown, FL 67890",
            "phone_number": "555-456-7890",
            "email": "michael.johnson@example.com",
            "blood_type": "B+",
            "disease_history": "Seasonal allergies",
            "medication_history": "Cetirizine 10mg daily during pollen season",
            "allergies": "None known"
        },
        {
            "first_name": "Sarah",
            "last_name": "Williams",
            "age": 65,
            "sex": "F",
            "address": "101 Elm St, Lasttown, TX 13579",
            "phone_number": "555-246-8102",
            "email": "sarah.williams@example.com",
            "blood_type": "AB+",
            "disease_history": "Hypertension, Osteoarthritis, GERD",
            "medication_history": "Losartan 50mg daily, Omeprazole 20mg daily, Acetaminophen as needed",
            "allergies": "Ibuprofen, Aspirin"
        }
    ]
    
    created_patients = []
    for patient_data in patients:
        patient, created = Patient.objects.get_or_create(
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            defaults={
                "age": patient_data["age"],
                "sex": patient_data["sex"],
                "address": patient_data["address"],
                "phone_number": patient_data["phone_number"],
                "email": patient_data["email"],
                "blood_type": patient_data["blood_type"],
                "disease_history": patient_data["disease_history"],
                "medication_history": patient_data["medication_history"],
                "allergies": patient_data["allergies"]
            }
        )
        
        created_patients.append(patient)
        if created:
            print(f"Created patient: {patient.first_name} {patient.last_name}")
        else:
            print(f"Patient already exists: {patient.first_name} {patient.last_name}")
    
    return created_patients

def create_sales(patients, drugs):
    if not User.objects.filter(username='admin').exists():
        print("Admin user not found, cannot create sales")
        return
    
    admin_user = User.objects.get(username='admin')
    
    for i in range(10):
        # Create sales with varying dates over the past month
        sale_date = timezone.now() - timedelta(days=random.randint(0, 30))
        
        # Select a random patient or None for walk-in customer
        patient = random.choice(patients) if random.random() > 0.2 else None
        
        # Create the sale record
        sale = Sale.objects.create(
            patient=patient,
            user=admin_user,
            date=sale_date,
            payment_method=random.choice(['Cash', 'Card', 'Mobile Payment']),
            payment_status='Paid',
            discount=random.choice([0, 5, 10, 15])
        )
        
        # Add between 1 and 4 items to the sale
        num_items = random.randint(1, 4)
        selected_drugs = random.sample(drugs, num_items)
        
        subtotal = 0
        for drug in selected_drugs:
            quantity = random.randint(1, 3)
            price = drug.selling_price
            
            # Create sale item
            SaleItem.objects.create(
                sale=sale,
                drug=drug,
                drug_name=drug.name,
                quantity=quantity,
                price=price
            )
            
            subtotal += price * quantity
        
        # Calculate totals
        discount_amount = (subtotal * sale.discount) / 100
        tax = subtotal * 0.08  # 8% tax
        total = subtotal - discount_amount + tax
        
        # Update sale with totals
        sale.subtotal = subtotal
        sale.tax = tax
        sale.total_amount = total
        sale.save()
        
        print(f"Created sale: {sale.invoice_number} with {num_items} items, total: ${total:.2f}")

def main():
    print("Creating test data...")
    categories = create_drug_categories()
    drugs = create_drugs(categories)
    create_drug_interactions(drugs)
    patients = create_patients()
    create_sales(patients, drugs)
    print("Test data creation complete!")

if __name__ == "__main__":
    main()