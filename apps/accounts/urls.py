# apps/accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication - using Django's built-in views
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='accounts:login'
    ), name='logout'),
    
    # Only include URLs for views that actually exist
    # Remove or comment out the others until you create them
]