# apps/accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    CreateView, DetailView, UpdateView, ListView, TemplateView, DeleteView
)
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from .models import User, UserProfile
from .forms import CustomUserCreationForm, UserProfileForm, UserUpdateForm

User = get_user_model()


class RegisterView(CreateView):
    """User registration view"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        """Process valid form and auto-login user"""
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        
        if user:
            login(self.request, user)
            messages.success(
                self.request,
                f'Welcome {user.get_full_name()}! Your account has been created successfully.'
            )
            return redirect('core:dashboard')  # Change this to your dashboard URL
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Register - OAPI Canteen'
        return context


class CustomLoginView(LoginView):
    """Custom login view with additional functionality"""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect based on user role"""
        user = self.request.user
        if user.role == 'SYSTEM_ADMIN':
            return reverse('admin:index')
        elif user.can_manage_orders():
            return reverse('core:dashboard')  # Change to your dashboard URL
        else:
            return reverse('core:dashboard')  # Change to your dashboard URL
    
    def form_valid(self, form):
        """Add welcome message on successful login"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Welcome back, {self.request.user.get_full_name()}!'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login - OAPI Canteen'
        return context


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = 'accounts:login'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        """Get user profile - own profile or specified user (for admins)"""
        pk = self.kwargs.get('pk')
        if pk and self.request.user.can_manage_users():
            return get_object_or_404(User, pk=pk)
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['title'] = f'{user.get_full_name()} - Profile'
        context['is_own_profile'] = user == self.request.user
        context['can_edit'] = (
            user == self.request.user or 
            self.request.user.can_manage_users()
        )
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile view"""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/profile_edit.html'
    
    def get_object(self):
        """Get user to edit - own profile or specified user (for admins)"""
        pk = self.kwargs.get('pk')
        if pk and self.request.user.can_manage_users():
            return get_object_or_404(User, pk=pk)
        return self.request.user
    
    def get_success_url(self):
        return reverse('accounts:profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['title'] = f'Edit Profile - {user.get_full_name()}'
        context['profile_user'] = user
        return context


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """User settings view for managing preferences"""
    template_name = 'accounts/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['title'] = 'Settings'
        context['user'] = user
        context['profile'], _ = UserProfile.objects.get_or_create(user=user)
        return context


class UserListView(LoginRequiredMixin, ListView):
    """List all users - Admin only"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_users():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return User.objects.select_related('profile').all().order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'User Management'
        context['total_users'] = self.get_queryset().count()
        return context


class UserCreateView(LoginRequiredMixin, CreateView):
    """Create new user - Admin only"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_create.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_users():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('accounts:user_list')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'User {form.cleaned_data["username"]} created successfully!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New User'
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    """User detail view - Admin only"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'profile_user'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_users():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['title'] = f'{user.get_full_name()} - User Details'
        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    """Edit user - Admin only"""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_edit.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_users():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('accounts:user_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'User {form.instance.get_full_name()} updated successfully!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit User - {self.object.get_full_name()}'
        return context


class UserDeleteView(LoginRequiredMixin, DeleteView):
    """Delete user - Admin only"""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_users():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('accounts:user_list')
        
        username = user.get_full_name()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'User {username} has been deleted.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Delete User - {self.object.get_full_name()}'
        return context


# API Views
@login_required
def check_username_api(request):
    """API endpoint to check if username is available"""
    username = request.GET.get('username', '').strip()
    
    if not username:
        return JsonResponse({'available': False, 'message': 'Username is required'})
    
    if len(username) < 3:
        return JsonResponse({'available': False, 'message': 'Username must be at least 3 characters'})
    
    # Check if username exists
    if User.objects.filter(username=username).exists():
        return JsonResponse({'available': False, 'message': 'Username is already taken'})
    
    return JsonResponse({'available': True, 'message': 'Username is available'})