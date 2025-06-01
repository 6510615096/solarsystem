from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Drone controller', 'Drone controller'),
        ('Admin solar', 'Admin solar'),
        ('Data analyst', 'Data analyst'),
    ]
    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class SolarPlant(models.Model):
    STATUS_CHOICES = [
        ("In process", "In process"),
        ("Completed", "Completed"),
        ("Delayed", "Delayed"),
    ]
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_plants')
    collected_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    weather = models.CharField(max_length=100, blank=True, null=True)
    temperature = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()

    # ✅ เพิ่ม latitude และ longitude เพื่อเก็บพิกัด
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    invited_emails = models.TextField(blank=True, null=True)
    properties = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_users = models.ManyToManyField(User, related_name='plants', blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="In process",
    )

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.ManyToManyField(Role, blank=True, related_name='users')
    assigned_plants = models.ManyToManyField(SolarPlant, blank=True, related_name='users')
    
    def __str__(self):
        return f"{self.user.username} - {', '.join([role.name for role in self.roles.all()])}"
    
    def get_roles_display(self):
        return ", ".join([role.name for role in self.roles.all()])


class UploadedFile(models.Model):
    plant = models.ForeignKey('SolarPlant', on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    weather = models.CharField(max_length=100, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    collected_date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    zone = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.file.name} → {self.plant.name}"
