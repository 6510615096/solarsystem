from .models import UserProfile

def create_user_profile(backend, user, response, *args, **kwargs):

    if not hasattr(user, 'profile'):
        profile = UserProfile.objects.create(user=user)