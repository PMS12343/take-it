from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import (
    Drug, DrugCategory, Patient, Sale, SaleItem, 
    InventoryLog, DrugInteraction, UserProfile
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
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'})
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
        fields = ['name', 'brand', 'description', 'category', 'stock_quantity', 
                  'cost_price', 'selling_price', 'reorder_level', 'expiry_date', 
                  'batch_number', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
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
    class Meta:
        model = Sale
        fields = ['patient', 'payment_method', 'payment_status', 'discount', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_status': forms.TextInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

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
