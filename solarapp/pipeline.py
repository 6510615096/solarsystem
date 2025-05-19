from django.core.exceptions import PermissionDenied
from social_core.exceptions import AuthForbidden
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from solarapp.models import UserProfile

def strict_social_user(strategy, uid, provider=None, user=None, *args, **kwargs):
    from social_django.models import UserSocialAuth
    from social_core.exceptions import AuthForbidden

    try:
        social = UserSocialAuth.objects.get(uid=uid, provider=provider)
        user = social.user

        # บล็อก superuser ไม่ให้ login ผ่าน Google
        if user.is_superuser:
            raise AuthForbidden("Google login not allowed for superuser.")

        return {'social': social, 'user': user}
    except UserSocialAuth.DoesNotExist:
        return {'user': None}

def get_user_by_email_if_exists(strategy, details, *args, **kwargs):
    email = details.get('email')
    if not email:
        raise AuthForbidden("Email not provided by Google.")

    try:
        user = User.objects.get(username=email)  # สมมุติว่า username == email ตอนสมัคร
        return {'user': user}
    except User.DoesNotExist:
        return {'user': None}

def reject_email_conflict(strategy, details, *args, **kwargs):
    email = details.get('email')
    if not email:
        raise AuthForbidden("Google account must have an email.")

    if User.objects.filter(username=email).exists():
        raise AuthForbidden("This email is already registered. Please login using password.")

def create_user_profile(backend, user=None, response=None, *args, **kwargs):
    if user is None:
        return

    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user)

    if not user.is_superuser:
        user.is_active = False
        user.save()

    if not user.profile.roles.exists():
        raise PermissionDenied("Your account has been created but is pending approval.")

def prevent_social_linking_to_superuser(backend, user, *args, **kwargs):
    if user and user.is_superuser:
        raise PermissionDenied("Cannot link Google account to superuser.")
