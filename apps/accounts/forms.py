# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+237XXXXXXXXX'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    employee_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'employee_id', 'role'
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        
        # Only system admins can assign admin roles
        if hasattr(self, 'request') and self.request.user.role != 'SYSTEM_ADMIN':
            self.fields['role'].choices = [
                ('USER', 'User'),
                ('CANTEEN_MANAGER', 'Canteen Manager'),
            ]


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    
    class Meta:
        model = UserProfile
        fields = (
            'bio', 'birth_date', 'address', 'emergency_contact',
            'emergency_phone', 'dietary_restrictions', 'preferred_payment_method'
        )
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'dietary_restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'preferred_payment_method': forms.Select(attrs={'class': 'form-select'}),
        }


class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'phone',
            'department', 'employee_id', 'avatar'
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }