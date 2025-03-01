from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.ManyToManyField(Role, blank=True, related_name='users')
    
    def __str__(self):
        return f"{self.user.username} - {', '.join([role.name for role in self.roles.all()])}"
    
    def get_roles_display(self):
        return ", ".join([role.name for role in self.roles.all()])