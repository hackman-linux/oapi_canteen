# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""
    
    list_display = (
        'username', 'email', 'get_full_name', 'role',
        'is_active_employee', 'date_joined', 'role_badge'
    )
    list_filter = (
        'role', 'is_active', 'is_active_employee',
        'is_staff', 'date_joined'
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': (
                'role', 'phone', 'department',
                'employee_id', 'avatar', 'is_active_employee'
            )
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': (
                'role', 'phone', 'department',
                'employee_id', 'first_name', 'last_name', 'email'
            )
        }),
    )
    
    def role_badge(self, obj):
        """Display role as colored badge"""
        badge_info = obj.get_role_display_badge()
        return format_html(
            '<span class="badge {}">{}</span>',
            badge_info['class'],
            badge_info['role']
        )
    role_badge.short_description = 'Role'
    role_badge.admin_order_field = 'role'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model"""
    
    list_display = (
        'user', 'preferred_payment_method', 'get_age_display', 'created_at'
    )
    list_filter = ('preferred_payment_method', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Details', {
            'fields': ('bio', 'birth_date', 'address', 'dietary_restrictions')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Preferences', {
            'fields': ('preferred_payment_method', 'notification_preferences')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_age_display(self, obj):
        """Display user's age"""
        age = obj.get_age()
        return f"{age} years" if age else "Not specified"
    get_age_display.short_description = 'Age'
