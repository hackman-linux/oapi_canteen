# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from PIL import Image


class User(AbstractUser):
    """Custom User model with role-based permissions"""
    
    class UserRole(models.TextChoices):
        USER = 'USER', 'User'
        CANTEEN_MANAGER = 'CANTEEN_MANAGER', 'Canteen Manager'
        SYSTEM_ADMIN = 'SYSTEM_ADMIN', 'System Admin'
        CANTEEN_ADMIN = 'CANTEEN_ADMIN', 'Canteen Admin'
    
    # Additional fields
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
        help_text="User role for permission management"
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Phone number for mobile money payments"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Department or division"
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Employee identification number"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Profile picture"
    )
    is_active_employee = models.BooleanField(
        default=True,
        help_text="Whether the employee is currently active"
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'pk': self.pk})
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username
    
    def get_role_display_badge(self):
        """Return role with appropriate CSS class for badges"""
        role_classes = {
            self.UserRole.USER: 'badge-primary',
            self.UserRole.CANTEEN_MANAGER: 'badge-success',
            self.UserRole.SYSTEM_ADMIN: 'badge-danger',
            self.UserRole.CANTEEN_ADMIN: 'badge-warning',
        }
        return {
            'role': self.get_role_display(),
            'class': role_classes.get(self.role, 'badge-secondary')
        }
    
    def can_manage_orders(self):
        """Check if user can manage orders"""
        return self.role in [self.UserRole.CANTEEN_MANAGER, self.UserRole.CANTEEN_ADMIN]
    
    def can_manage_menu(self):
        """Check if user can manage menu items"""
        return self.role in [self.UserRole.CANTEEN_ADMIN, self.UserRole.SYSTEM_ADMIN]
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role == self.UserRole.SYSTEM_ADMIN
    
    def can_view_reports(self):
        """Check if user can view reports"""
        return self.role in [
            self.UserRole.CANTEEN_MANAGER,
            self.UserRole.CANTEEN_ADMIN,
            self.UserRole.SYSTEM_ADMIN
        ]
    
    def save(self, *args, **kwargs):
        """Override save to resize avatar image"""
        super().save(*args, **kwargs)
        
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)


class UserProfile(models.Model):
    """Extended profile information for users"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Brief biography or description"
    )
    birth_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date of birth"
    )
    address = models.TextField(
        blank=True,
        help_text="Home address"
    )
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        help_text="Emergency contact person"
    )
    emergency_phone = models.CharField(
        max_length=15,
        blank=True,
        help_text="Emergency contact phone number"
    )
    dietary_restrictions = models.TextField(
        blank=True,
        help_text="Any dietary restrictions or allergies"
    )
    preferred_payment_method = models.CharField(
        max_length=20,
        choices=[
            ('ORANGE', 'Orange Money'),
            ('MTN', 'MTN Mobile Money'),
            ('CASH', 'Cash'),
        ],
        default='ORANGE',
        help_text="Preferred payment method"
    )
    notification_preferences = models.JSONField(
        default=dict,
        help_text="User notification preferences"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
    
    def get_age(self):
        """Calculate user's age from birth_date"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None