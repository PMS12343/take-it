from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import (
    Drug, DrugCategory, Patient, Sale, SaleItem, 
    InventoryLog, DrugInteraction, UserProfile, Supplier,
    InvoiceUpload, InvoiceItem
)

class UserLoginForm(AuthenticationForm):
    """Form for user login"""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'validate',
        'placeholder': 'Username',
        'id': 'id_username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'validate',
        'placeholder': 'Password',
        'id': 'id_password'
    }))

class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Form for user profile"""
    class Meta:
        model = UserProfile
        fields = ['role', 'dark_mode']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'dark_mode': forms.CheckboxInput(attrs={'class': 'filled-in'})
        }

class DrugCategoryForm(forms.ModelForm):
    """Form for drug categories"""
    class Meta:
        model = DrugCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DrugForm(forms.ModelForm):
    """Form for adding/editing drugs"""
    class Meta:
        model = Drug
        fields = ['name', 'brand', 'barcode', 'description', 'category', 'stock_quantity', 
                  'cost_price', 'selling_price', 'reorder_level', 'expiry_date', 
                  'batch_number', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or enter barcode (optional)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date < timezone.now().date():
            raise forms.ValidationError("Expiry date cannot be in the past.")
        return expiry_date
    
    def clean(self):
        cleaned_data = super().clean()
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')
        
        if cost_price and selling_price and cost_price > selling_price:
            self.add_error('selling_price', "Selling price must be greater than or equal to cost price.")
        
        return cleaned_data

class PatientForm(forms.ModelForm):
    """Form for adding/editing patients"""
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'age', 'sex', 'address', 
                 'phone_number', 'email', 'blood_type', 'disease_history', 
                 'medication_history', 'allergies']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'disease_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medication_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SaleForm(forms.ModelForm):
    """Form for creating sales"""
    use_walk_in = forms.BooleanField(
        required=False, 
        label="Walk-In Customer",
        widget=forms.CheckboxInput(attrs={'class': 'filled-in'})
    )
    
    class Meta:
        model = Sale
        fields = ['patient', 'payment_method', 'payment_status', 'tax', 'discount', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_status': forms.TextInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        # Initialize tax with zero if it's a new form
        if not self.instance.pk and not self.initial.get('tax'):
            self.initial['tax'] = 0.00
            
    def clean(self):
        cleaned_data = super().clean()
        use_walk_in = cleaned_data.get('use_walk_in')
        patient = cleaned_data.get('patient')
        
        # If walk-in is selected but no patient is provided, this will be handled in the view
        # by assigning the walk-in customer automatically
        if use_walk_in:
            # Remove any validation errors for patient field if walk-in is selected
            if 'patient' in self.errors:
                del self.errors['patient']
            # Set patient to None so we know to use walk-in in the view
            cleaned_data['patient'] = None
            
        return cleaned_data

class SaleItemForm(forms.ModelForm):
    """Form for individual sale items"""
    class Meta:
        model = SaleItem
        fields = ['drug', 'quantity']
        widgets = {
            'drug': forms.Select(attrs={'class': 'form-control drug-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        drug = self.cleaned_data.get('drug')
        
        if quantity and drug and quantity > drug.stock_quantity:
            raise forms.ValidationError(f"Available stock: {drug.stock_quantity}")
        
        return quantity

# Create a formset for SaleItems
SaleItemFormSet = inlineformset_factory(
    Sale, SaleItem, form=SaleItemForm,
    extra=1, can_delete=True,
    fields=['drug', 'quantity'],
)

class DrugInteractionForm(forms.ModelForm):
    """Form for drug interactions"""
    class Meta:
        model = DrugInteraction
        fields = ['drug_one', 'drug_two', 'severity', 'description']
        widgets = {
            'drug_one': forms.Select(attrs={'class': 'form-control'}),
            'drug_two': forms.Select(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        drug_one = cleaned_data.get('drug_one')
        drug_two = cleaned_data.get('drug_two')
        
        if drug_one and drug_two and drug_one == drug_two:
            raise forms.ValidationError("Cannot create an interaction between the same drug.")
        
        return cleaned_data

class DateRangeForm(forms.Form):
    """Form for specifying date ranges in reports"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data


class DrugImportForm(forms.Form):
    """Form for importing drugs from Excel"""
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload an Excel file (.xlsx)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
    )
    
    
class SupplierForm(forms.ModelForm):
    """Form for adding/editing suppliers"""
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'address', 'email', 'phone', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InvoiceUploadForm(forms.ModelForm):
    """Form for uploading invoices"""
    class Meta:
        model = InvoiceUpload
        fields = ['supplier', 'invoice_number', 'invoice_date', 'file']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional - will be extracted if possible'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png,.xlsx,.xls'}),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            extension = file.name.split('.')[-1].lower()
            if extension not in ['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls']:
                raise forms.ValidationError("Unsupported file format. Please upload a PDF, image, or Excel file.")
            
            # Set the file type based on the extension
            if extension in ['pdf']:
                self.instance.file_type = 'PDF'
            elif extension in ['jpg', 'jpeg', 'png']:
                self.instance.file_type = 'IMAGE'
            elif extension in ['xlsx', 'xls']:
                self.instance.file_type = 'EXCEL'
                
        return file


class InvoiceItemMatchForm(forms.ModelForm):
    """Form for matching extracted invoice items to drugs"""
    class Meta:
        model = InvoiceItem
        fields = ['matched_drug', 'quantity', 'cost_price', 'match_status']
        widgets = {
            'matched_drug': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'match_status': forms.Select(attrs={'class': 'form-control'}),
        }
