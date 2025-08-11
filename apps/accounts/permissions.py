# apps/accounts/permissions.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps


def role_required(*roles):
    """Decorator to require specific user roles"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if request.user.role not in roles:
                raise PermissionDenied("You don't have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def canteen_manager_required(view_func):
    """Decorator for canteen manager only views"""
    return role_required('CANTEEN_MANAGER')(view_func)


def system_admin_required(view_func):
    """Decorator for system admin only views"""
    return role_required('SYSTEM_ADMIN')(view_func)


def canteen_admin_required(view_func):
    """Decorator for canteen admin only views"""
    return role_required('CANTEEN_ADMIN')(view_func)


def staff_required(view_func):
    """Decorator for staff members (managers and admins)"""
    return role_required(
        'CANTEEN_MANAGER', 'SYSTEM_ADMIN', 'CANTEEN_ADMIN'
    )(view_func)


class RoleRequiredMixin:
    """Mixin for class-based views to require specific roles"""
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if self.required_roles and request.user.role not in self.required_roles:
            raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)
