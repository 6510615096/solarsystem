from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Role

@receiver(post_save, sender=User)
def assign_admin_role_to_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        admin_role, _ = Role.objects.get_or_create(name='Admin')
        profile.roles.add(admin_role)
