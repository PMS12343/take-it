from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import Drug, Patient, Sale, SaleItem, DrugInteraction


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(UserCreationForm):
    role = forms.ModelChoiceField(queryset=Group.objects.all(), required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role')


class DrugForm(forms.ModelForm):
    class Meta:
        model = Drug
        fields = ('name', 'brand', 'description', 'quantity', 'reorder_level', 
                  'cost_price', 'selling_price', 'expiry_date')
        widgets = {
            'expiry_date': forms.DateInput(attrs={'class': 'datepicker'}),
            'description': forms.Textarea(attrs={'class': 'materialize-textarea'}),
        }


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ('name', 'age', 'sex', 'address', 'phone', 'email', 
                  'blood_type', 'disease_history', 'medication_history')
        widgets = {
            'disease_history': forms.Textarea(attrs={'class': 'materialize-textarea'}),
            'medication_history': forms.Textarea(attrs={'class': 'materialize-textarea'}),
        }


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ('patient',)


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ('drug', 'quantity')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only drugs that are in stock
        self.fields['drug'].queryset = Drug.objects.filter(quantity__gt=0)
    
    def clean_quantity(self):
        drug = self.cleaned_data.get('drug')
        quantity = self.cleaned_data.get('quantity')
        
        if drug and quantity:
            if quantity > drug.quantity:
                raise forms.ValidationError(f"Only {drug.quantity} units of {drug.name} available.")
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than zero.")
        
        return quantity


class DrugInteractionForm(forms.ModelForm):
    class Meta:
        model = DrugInteraction
        fields = ('drug1', 'drug2', 'description', 'severity')
        widgets = {
            'description': forms.Textarea(attrs={'class': 'materialize-textarea'}),
        }


class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'datepicker'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'datepicker'}))


class SaleItemFormSet(forms.BaseFormSet):
    def clean(self):
        """
        Validate that at least one item is selected for sale
        """
        if any(self.errors):
            return
        
        if not any(form.cleaned_data for form in self.forms):
            raise forms.ValidationError("At least one drug must be selected for sale.")
