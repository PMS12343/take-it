from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Sum, Count, F, Q, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, TruncDay
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import get_template
from datetime import datetime, timedelta
import json
import decimal
import csv
import xlsxwriter
from io import BytesIO

from .models import (
    Drug, DrugCategory, Patient, Sale, SaleItem, 
    InventoryLog, DrugInteraction, UserProfile
)
from .forms import (
    UserLoginForm, UserRegistrationForm, UserProfileForm,
    DrugForm, PatientForm, SaleForm, SaleItemFormSet,
    DrugInteractionForm, DateRangeForm
)
from .utils import (
    render_to_pdf, check_role_permission, get_low_stock_drugs,
    get_expiring_drugs, requires_role
)

# Authentication Views
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt with username: {username}")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"Authentication successful for user: {username}")
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            print(f"Authentication failed for user: {username}")
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def profile_view(request):
    """Display and update user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'profile.html', {'form': form})

# Dashboard Views
@login_required
def dashboard(request):
    """Main dashboard showing key metrics and notifications"""
    # Get counts for main entities
    drugs_count = Drug.objects.filter(is_active=True).count()
    patients_count = Patient.objects.count()
    sales_count = Sale.objects.count()
    
    # Get low stock and expiring medications
    low_stock_drugs = get_low_stock_drugs()
    expiring_drugs = get_expiring_drugs()
    
    # Calculate revenue stats
    today = timezone.now().date()
    today_sales = Sale.objects.filter(date__date=today).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Get this month's sales data
    month_start = today.replace(day=1)
    month_sales = Sale.objects.filter(date__date__gte=month_start).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Get recent sales
    recent_sales = Sale.objects.select_related('patient', 'user').order_by('-date')[:5]
    
    # Get top selling drugs this month
    top_drugs = SaleItem.objects.filter(sale__date__date__gte=month_start)\
        .values('drug_name')\
        .annotate(total_quantity=Sum('quantity'))\
        .order_by('-total_quantity')[:5]
    
    # Context data
    context = {
        'drugs_count': drugs_count,
        'patients_count': patients_count,
        'sales_count': sales_count,
        'low_stock_drugs': low_stock_drugs,
        'expiring_drugs': expiring_drugs,
        'today_sales': today_sales,
        'month_sales': month_sales,
        'recent_sales': recent_sales,
        'top_drugs': top_drugs,
    }
    
    return render(request, 'dashboard.html', context)

# Drug Management Views
@login_required
@requires_role(['Admin', 'Pharmacist', 'Manager'])
def drug_list(request):
    """List all drugs with search and filter functionality"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('stock_status', '')
    expiry_status = request.GET.get('expiry_status', '')
    
    drugs = Drug.objects.all()
    
    # Apply filters
    if query:
        drugs = drugs.filter(Q(name__icontains=query) | Q(brand__icontains=query))
    
    if category_id:
        drugs = drugs.filter(category_id=category_id)
    
    if stock_status == 'low':
        drugs = drugs.filter(stock_quantity__lte=F('reorder_level'))
    elif stock_status == 'out':
        drugs = drugs.filter(stock_quantity=0)
    
    if expiry_status == 'expiring':
        today = timezone.now().date()
        two_months_later = today + timedelta(days=60)
        drugs = drugs.filter(expiry_date__gt=today, expiry_date__lte=two_months_later)
    elif expiry_status == 'expired':
        drugs = drugs.filter(expiry_date__lt=timezone.now().date())
    
    # Get categories for filter dropdown
    categories = DrugCategory.objects.all()
    
    context = {
        'drugs': drugs,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'stock_status': stock_status,
        'expiry_status': expiry_status,
    }
    
    return render(request, 'drugs/list.html', context)

@login_required
@requires_role(['Admin', 'Pharmacist'])
def drug_add(request):
    """Add a new drug to the inventory"""
    if request.method == 'POST':
        form = DrugForm(request.POST)
        if form.is_valid():
            drug = form.save()
            
            # Log the inventory addition
            InventoryLog.objects.create(
                drug=drug,
                quantity_change=drug.stock_quantity,
                operation_type='ADD',
                notes="Initial stock when drug was added",
                user=request.user
            )
            
            messages.success(request, f"Drug {drug.name} added successfully.")
            return redirect('drug_list')
    else:
        form = DrugForm()
    
    return render(request, 'drugs/add.html', {'form': form})

@login_required
@requires_role(['Admin', 'Pharmacist'])
def drug_edit(request, drug_id):
    """Edit an existing drug"""
    drug = get_object_or_404(Drug, id=drug_id)
    original_quantity = drug.stock_quantity
    
    if request.method == 'POST':
        form = DrugForm(request.POST, instance=drug)
        if form.is_valid():
            updated_drug = form.save()
            
            # If stock quantity changed, log it
            new_quantity = updated_drug.stock_quantity
            if new_quantity != original_quantity:
                quantity_change = new_quantity - original_quantity
                InventoryLog.objects.create(
                    drug=updated_drug,
                    quantity_change=quantity_change,
                    operation_type='ADJUST',
                    notes="Stock adjustment during drug edit",
                    user=request.user
                )
            
            messages.success(request, f"Drug {updated_drug.name} updated successfully.")
            return redirect('drug_list')
    else:
        form = DrugForm(instance=drug)
    
    return render(request, 'drugs/edit.html', {'form': form, 'drug': drug})

@login_required
@requires_role(['Admin', 'Pharmacist', 'Manager', 'Sales Clerk'])
def drug_detail(request, drug_id):
    """Display detailed information about a drug"""
    drug = get_object_or_404(Drug, id=drug_id)
    
    # Get transaction history for this drug
    inventory_logs = InventoryLog.objects.filter(drug=drug).order_by('-timestamp')[:20]
    
    # Get drug interactions
    interactions = DrugInteraction.objects.filter(
        Q(drug_one=drug) | Q(drug_two=drug)
    ).select_related('drug_one', 'drug_two')
    
    context = {
        'drug': drug,
        'inventory_logs': inventory_logs,
        'interactions': interactions,
    }
    
    return render(request, 'drugs/detail.html', context)

# Patient Management Views
@login_required
def patient_list(request):
    """List all patients with search functionality"""
    query = request.GET.get('q', '')
    
    patients = Patient.objects.all()
    
    if query:
        patients = patients.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        )
    
    return render(request, 'patients/list.html', {'patients': patients, 'query': query})

@login_required
@requires_role(['Admin', 'Pharmacist', 'Manager'])
def patient_add(request):
    """Add a new patient"""
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"Patient {patient.full_name} added successfully.")
            return redirect('patient_list')
    else:
        form = PatientForm()
    
    return render(request, 'patients/add.html', {'form': form})

@login_required
@requires_role(['Admin', 'Pharmacist', 'Manager'])
def patient_edit(request, patient_id):
    """Edit an existing patient"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            updated_patient = form.save()
            messages.success(request, f"Patient {updated_patient.full_name} updated successfully.")
            return redirect('patient_list')
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'patients/edit.html', {'form': form, 'patient': patient})

@login_required
def patient_detail(request, patient_id):
    """Display detailed information about a patient"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get patient's purchase history
    sales = Sale.objects.filter(patient=patient).order_by('-date')
    
    context = {
        'patient': patient,
        'sales': sales,
    }
    
    return render(request, 'patients/detail.html', context)

# Sales Management Views
@login_required
@requires_role(['Admin', 'Pharmacist', 'Sales Clerk'])
def new_sale(request):
    """Create a new sale transaction"""
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.user = request.user
            sale.save()
            
            formset = SaleItemFormSet(request.POST, instance=sale)
            if formset.is_valid():
                # Validate stock availability before saving
                items_valid = True
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        drug = form.cleaned_data.get('drug')
                        quantity = form.cleaned_data.get('quantity')
                        
                        if drug and drug.stock_quantity < quantity:
                            messages.error(request, f"Not enough stock for {drug.name}. Available: {drug.stock_quantity}")
                            items_valid = False
                            break
                
                if items_valid:
                    # Save the formset
                    items = formset.save(commit=False)
                    
                    # Calculate sale totals
                    subtotal = decimal.Decimal('0.00')
                    for item in items:
                        item.drug_name = item.drug.name if item.drug else "Unknown Drug"
                        item.price = item.drug.selling_price if item.drug else decimal.Decimal('0.00')
                        item.save()
                        subtotal += item.price * item.quantity
                    
                    # Apply tax and discount calculations
                    tax_amount = subtotal * decimal.Decimal('0.10')  # 10% tax example
                    sale.subtotal = subtotal
                    sale.tax = tax_amount
                    sale.total_amount = subtotal + tax_amount - sale.discount
                    sale.save()
                    
                    # Check for drug interactions
                    interactions = check_drug_interactions(sale)
                    if interactions:
                        # Store in session to display on next page
                        request.session['interaction_warnings'] = interactions
                    
                    messages.success(request, f"Sale recorded successfully. Invoice #: {sale.invoice_number}")
                    return redirect('sale_detail', sale_id=sale.id)
                else:
                    # If any item validation failed, delete the sale
                    sale.delete()
            else:
                messages.error(request, "There was an error with the sale items.")
                sale.delete()
        else:
            messages.error(request, "There was an error with the sale information.")
    else:
        form = SaleForm()
        formset = SaleItemFormSet()
    
    # Get all active drugs for the form
    drugs = Drug.objects.filter(is_active=True, stock_quantity__gt=0)
    patients = Patient.objects.all()
    
    context = {
        'form': form,
        'formset': formset,
        'drugs': drugs,
        'patients': patients,
    }
    
    return render(request, 'sales/new.html', context)

def check_drug_interactions(sale):
    """Check for drug interactions among items in a sale"""
    interactions = []
    sale_items = sale.saleitems.all()
    drugs = [item.drug for item in sale_items if item.drug]
    
    # Check each pair of drugs
    for i in range(len(drugs)):
        for j in range(i+1, len(drugs)):
            drug1, drug2 = drugs[i], drugs[j]
            
            # Check for interactions in both directions
            interaction = DrugInteraction.objects.filter(
                (Q(drug_one=drug1) & Q(drug_two=drug2)) | 
                (Q(drug_one=drug2) & Q(drug_two=drug1))
            ).first()
            
            if interaction and interaction.severity != 'NONE':
                interactions.append({
                    'drug1': drug1.name,
                    'drug2': drug2.name,
                    'severity': interaction.severity,
                    'description': interaction.description
                })
    
    return interactions

@login_required
def sale_list(request):
    """List all sales with search and filter functionality"""
    query = request.GET.get('q', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    sales = Sale.objects.all()
    
    # Apply filters
    if query:
        sales = sales.filter(
            Q(invoice_number__icontains=query) | 
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            sales = sales.filter(date__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            sales = sales.filter(date__date__lte=date_to)
        except ValueError:
            pass
    
    context = {
        'sales': sales,
        'query': query,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'sales/list.html', context)

@login_required
def sale_detail(request, sale_id):
    """Display detailed information about a sale"""
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.saleitems.all()
    
    # Get interaction warnings from session if any
    interaction_warnings = request.session.pop('interaction_warnings', None)
    
    context = {
        'sale': sale,
        'items': items,
        'interaction_warnings': interaction_warnings,
    }
    
    return render(request, 'sales/detail.html', context)

@login_required
def sale_invoice(request, sale_id):
    """Display and print invoice for a sale"""
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.saleitems.all()
    
    context = {
        'sale': sale,
        'items': items,
        'company_name': 'Pharmacy Management System',
        'company_address': '123 Health Street, Medical City',
        'company_phone': '+1 234 567 8900',
        'company_email': 'info@pharmacymanagement.com',
    }
    
    # Check if PDF generation is requested
    if 'pdf' in request.GET:
        pdf = render_to_pdf('sales/invoice.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Invoice_{sale.invoice_number}.pdf"
            content = f"inline; filename={filename}"
            response['Content-Disposition'] = content
            return response
    
    return render(request, 'sales/invoice.html', context)

# Report Views
@login_required
@requires_role(['Admin', 'Manager'])
def reports_index(request):
    """Display available reports"""
    return render(request, 'reports/index.html')

@login_required
@requires_role(['Admin', 'Manager'])
def sales_report(request):
    """Generate sales report based on date range"""
    form = DateRangeForm(request.GET or None)
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    else:
        # Default to current month
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today
    
    # Filter sales by date range
    sales = Sale.objects.filter(date__date__gte=start_date, date__date__lte=end_date)
    
    # Calculate summary statistics
    total_sales = sales.count()
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_sale_value = total_revenue / total_sales if total_sales > 0 else 0
    
    # Daily sales breakdown
    daily_sales = sales.annotate(
        day=TruncDay('date')
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('day')
    
    # Top selling drugs
    top_drugs = SaleItem.objects.filter(
        sale__date__date__gte=start_date,
        sale__date__date__lte=end_date
    ).values('drug_name').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('price'))
    ).order_by('-total_quantity')[:10]
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'avg_sale_value': avg_sale_value,
        'daily_sales': daily_sales,
        'top_drugs': top_drugs,
        'sales': sales,
    }
    
    # Check if export is requested
    if 'export' in request.GET:
        export_format = request.GET.get('export')
        if export_format == 'pdf':
            pdf = render_to_pdf('reports/sales_report.html', context)
            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = f"Sales_Report_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.pdf"
                content = f"attachment; filename={filename}"
                response['Content-Disposition'] = content
                return response
        elif export_format == 'excel':
            return export_sales_report_excel(sales, start_date, end_date)
        elif export_format == 'csv':
            return export_sales_report_csv(sales, start_date, end_date)
    
    return render(request, 'reports/sales_report.html', context)

def export_sales_report_excel(sales, start_date, end_date):
    """Export sales report as Excel file"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Sales Report')
    
    # Add header
    header_format = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2'})
    worksheet.write(0, 0, 'Invoice #', header_format)
    worksheet.write(0, 1, 'Date', header_format)
    worksheet.write(0, 2, 'Patient Name', header_format)
    worksheet.write(0, 3, 'Total Amount', header_format)
    worksheet.write(0, 4, 'Items Count', header_format)
    worksheet.write(0, 5, 'Payment Method', header_format)
    worksheet.write(0, 6, 'Status', header_format)
    
    # Add data
    for i, sale in enumerate(sales, 1):
        worksheet.write(i, 0, sale.invoice_number)
        worksheet.write(i, 1, sale.date.strftime('%Y-%m-%d %H:%M'))
        worksheet.write(i, 2, sale.patient.full_name if sale.patient else 'N/A')
        worksheet.write(i, 3, float(sale.total_amount))
        worksheet.write(i, 4, sale.item_count)
        worksheet.write(i, 5, sale.payment_method)
        worksheet.write(i, 6, sale.payment_status)
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Sales_Report_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

def export_sales_report_csv(sales, start_date, end_date):
    """Export sales report as CSV file"""
    response = HttpResponse(content_type='text/csv')
    filename = f"Sales_Report_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    writer = csv.writer(response)
    writer.writerow(['Invoice #', 'Date', 'Patient Name', 'Total Amount', 'Items Count', 'Payment Method', 'Status'])
    
    for sale in sales:
        writer.writerow([
            sale.invoice_number,
            sale.date.strftime('%Y-%m-%d %H:%M'),
            sale.patient.full_name if sale.patient else 'N/A',
            float(sale.total_amount),
            sale.item_count,
            sale.payment_method,
            sale.payment_status
        ])
    
    return response

@login_required
@requires_role(['Admin', 'Manager', 'Pharmacist'])
def inventory_report(request):
    """Generate inventory report"""
    form = DateRangeForm(request.GET or None)
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    else:
        # Default to current month
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today
    
    # Get all active drugs
    drugs = Drug.objects.filter(is_active=True)
    
    # Get total stock value
    total_stock_value = sum(drug.stock_quantity * drug.cost_price for drug in drugs)
    
    # Get low stock drugs
    low_stock_drugs = drugs.filter(stock_quantity__lte=F('reorder_level'))
    
    # Get expiring drugs (within 2 months)
    today = timezone.now().date()
    two_months_later = today + timedelta(days=60)
    expiring_drugs = drugs.filter(expiry_date__gt=today, expiry_date__lte=two_months_later)
    
    # Get inventory movement during the period
    inventory_logs = InventoryLog.objects.filter(
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).select_related('drug', 'user')
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'drugs': drugs,
        'total_stock_value': total_stock_value,
        'low_stock_drugs': low_stock_drugs,
        'expiring_drugs': expiring_drugs,
        'inventory_logs': inventory_logs,
    }
    
    # Check if export is requested
    if 'export' in request.GET:
        export_format = request.GET.get('export')
        if export_format == 'pdf':
            pdf = render_to_pdf('reports/inventory_report.html', context)
            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = f"Inventory_Report_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.pdf"
                content = f"attachment; filename={filename}"
                response['Content-Disposition'] = content
                return response
        elif export_format == 'excel':
            return export_inventory_report_excel(drugs, inventory_logs, start_date, end_date)
        elif export_format == 'csv':
            return export_inventory_report_csv(drugs, inventory_logs, start_date, end_date)
    
    return render(request, 'reports/inventory_report.html', context)

def export_inventory_report_excel(drugs, inventory_logs, start_date, end_date):
    """Export inventory report as Excel file"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Current Inventory sheet
    worksheet1 = workbook.add_worksheet('Current Inventory')
    header_format = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2'})
    
    # Headers
    worksheet1.write(0, 0, 'Drug Name', header_format)
    worksheet1.write(0, 1, 'Brand', header_format)
    worksheet1.write(0, 2, 'Category', header_format)
    worksheet1.write(0, 3, 'Current Stock', header_format)
    worksheet1.write(0, 4, 'Reorder Level', header_format)
    worksheet1.write(0, 5, 'Cost Price', header_format)
    worksheet1.write(0, 6, 'Selling Price', header_format)
    worksheet1.write(0, 7, 'Expiry Date', header_format)
    worksheet1.write(0, 8, 'Stock Value', header_format)
    
    # Data
    for i, drug in enumerate(drugs, 1):
        worksheet1.write(i, 0, drug.name)
        worksheet1.write(i, 1, drug.brand)
        worksheet1.write(i, 2, drug.category.name if drug.category else 'N/A')
        worksheet1.write(i, 3, drug.stock_quantity)
        worksheet1.write(i, 4, drug.reorder_level)
        worksheet1.write(i, 5, float(drug.cost_price))
        worksheet1.write(i, 6, float(drug.selling_price))
        worksheet1.write(i, 7, drug.expiry_date.strftime('%Y-%m-%d'))
        worksheet1.write(i, 8, float(drug.stock_quantity * drug.cost_price))
    
    # Inventory Movement sheet
    worksheet2 = workbook.add_worksheet('Inventory Movement')
    
    # Headers
    worksheet2.write(0, 0, 'Date', header_format)
    worksheet2.write(0, 1, 'Drug Name', header_format)
    worksheet2.write(0, 2, 'Quantity Change', header_format)
    worksheet2.write(0, 3, 'Operation Type', header_format)
    worksheet2.write(0, 4, 'Reference', header_format)
    worksheet2.write(0, 5, 'User', header_format)
    worksheet2.write(0, 6, 'Notes', header_format)
    
    # Data
    for i, log in enumerate(inventory_logs, 1):
        worksheet2.write(i, 0, log.timestamp.strftime('%Y-%m-%d %H:%M'))
        worksheet2.write(i, 1, log.drug.name if log.drug else 'N/A')
        worksheet2.write(i, 2, log.quantity_change)
        worksheet2.write(i, 3, log.get_operation_type_display())
        worksheet2.write(i, 4, log.reference or 'N/A')
        worksheet2.write(i, 5, log.user.username if log.user else 'N/A')
        worksheet2.write(i, 6, log.notes or 'N/A')
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Inventory_Report_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

def export_inventory_report_csv(drugs, inventory_logs, start_date, end_date):
    """Export inventory report as CSV file"""
    response = HttpResponse(content_type='text/csv')
    filename = f"Inventory_Report_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    writer = csv.writer(response)
    writer.writerow(['Drug Name', 'Brand', 'Category', 'Current Stock', 'Reorder Level', 
                     'Cost Price', 'Selling Price', 'Expiry Date', 'Stock Value'])
    
    for drug in drugs:
        writer.writerow([
            drug.name,
            drug.brand,
            drug.category.name if drug.category else 'N/A',
            drug.stock_quantity,
            drug.reorder_level,
            float(drug.cost_price),
            float(drug.selling_price),
            drug.expiry_date.strftime('%Y-%m-%d'),
            float(drug.stock_quantity * drug.cost_price)
        ])
    
    writer.writerow([])
    writer.writerow(['Inventory Movement:'])
    writer.writerow(['Date', 'Drug Name', 'Quantity Change', 'Operation Type', 'Reference', 'User', 'Notes'])
    
    for log in inventory_logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M'),
            log.drug.name if log.drug else 'N/A',
            log.quantity_change,
            log.get_operation_type_display(),
            log.reference or 'N/A',
            log.user.username if log.user else 'N/A',
            log.notes or 'N/A'
        ])
    
    return response

# User Management Views
@login_required
@requires_role(['Admin'])
def user_list(request):
    """List all users"""
    users = User.objects.select_related('profile').all()
    return render(request, 'users/list.html', {'users': users})

@login_required
@requires_role(['Admin'])
def user_add(request):
    """Add a new user"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = user.profile
            profile.role = profile_form.cleaned_data['role']
            profile.save()
            
            messages.success(request, f"User {user.username} added successfully.")
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
        profile_form = UserProfileForm()
    
    return render(request, 'users/add.html', {'form': form, 'profile_form': profile_form})

@login_required
@requires_role(['Admin'])
def user_edit(request, user_id):
    """Edit an existing user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user.profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} updated successfully.")
            return redirect('user_list')
    else:
        form = UserProfileForm(instance=user.profile)
    
    return render(request, 'users/edit.html', {'form': form, 'user': user})

# API endpoints for AJAX requests
@login_required
def get_drug_info(request, drug_id):
    """API to get drug information for sales form"""
    try:
        drug = Drug.objects.get(id=drug_id)
        data = {
            'id': drug.id,
            'name': drug.name,
            'brand': drug.brand,
            'price': float(drug.selling_price),
            'available_stock': drug.stock_quantity,
            'expiry_date': drug.expiry_date.strftime('%Y-%m-%d'),
            'is_expired': drug.is_expired(),
        }
        return JsonResponse(data)
    except Drug.DoesNotExist:
        return JsonResponse({'error': 'Drug not found'}, status=404)
