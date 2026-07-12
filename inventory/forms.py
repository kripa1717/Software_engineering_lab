from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, InventoryItem, Vendor, Order, StockLog


class RegisterForm(UserCreationForm):
    """R-1: User Registration"""
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')


class InventoryItemForm(forms.ModelForm):
    """R-3: Add Inventory Item"""
    class Meta:
        model = InventoryItem
        fields = ['name', 'unit', 'quantity', 'minThreshold', 'expirydate']
        widgets = {
            'expirydate': forms.DateInput(attrs={'type': 'date'}),
        }


class StockUpdateForm(forms.Form):
    """R-4: Update Stock Level"""
    quantity = forms.FloatField(min_value=0)
    changeType = forms.ChoiceField(choices=StockLog.CHANGE_TYPE_CHOICES)
    reason = forms.CharField(required=False, max_length=255)


class VendorForm(forms.ModelForm):
    """R-10: Add Vendor"""
    class Meta:
        model = Vendor
        fields = ['name', 'ContactNumber', 'email', 'qualityRating']


class OrderForm(forms.ModelForm):
    """R-12: Log Order History / place an order"""
    class Meta:
        model = Order
        fields = ['vendorId', 'itemId', 'quantity', 'totalCost', 'status']


class ReportFilterForm(forms.Form):
    """R-13/R-14: date range selection for reports"""
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
