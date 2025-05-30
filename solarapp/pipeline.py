from django.core.exceptions import PermissionDenied
from social_core.exceptions import AuthForbidden
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from solarapp.models import UserProfile
def prevent_superuser_social_login(strategy, uid, provider=None, user=None, *args, **kwargs):
    """Prevent superusers from logging in via social auth"""
    if user and user.is_superuser:
        raise AuthForbidden("Social authentication not allowed for admin accounts.")

def get_existing_user_by_email(strategy, details, *args, **kwargs):
    """Get existing user by email if exists"""
    email = details.get('email')
    if not email:
        raise AuthForbidden("Email not provided by social provider.")

    try:
        # Assuming username is email
        user = User.objects.get(email=email)
        return {'user': user}
    except User.DoesNotExist:
        return {'user': None}

def check_user_approval_status(strategy, user=None, *args, **kwargs):
    """Check if user is approved for login"""
    if not user:
        return
    
    # Allow superusers (but they shouldn't reach here due to prevent_superuser_social_login)
    if user.is_superuser:
        return
    
    # Check if user is active
    if not user.is_active:
        raise AuthForbidden("Your account is pending approval. Please wait for admin activation.")
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # MODIFIED: Allow login even without roles, but show warning
    if not profile.roles.exists():
        # Store a flag to show warning message after successful login
        strategy.session_set('show_no_roles_warning', True)

def create_user_profile_if_needed(backend, user=None, response=None, *args, **kwargs):
    """Create user profile for new social auth users"""
    if not user:
        return

    # Prevent superuser social linking
    if user.is_superuser:
        raise AuthForbidden("Cannot link social account to admin user.")

    # Create profile if doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # For new Google users, set inactive until admin approval
    if created:
        user.is_active = False
        user.save()
        raise AuthForbidden("Your account has been created but requires admin approval.")

def handle_new_social_user(strategy, details, *args, **kwargs):
    email = details.get('email')
    if not email:
        raise AuthForbidden("Social account must have an email address.")

    if User.objects.filter(email=email).exists():
        return
    
def strict_social_user(strategy, details, user=None, *args, **kwargs):
    if not user:
        return strategy.redirect('/login-error/')
    return {'user': user}
