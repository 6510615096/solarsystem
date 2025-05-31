from django.apps import AppConfig

class SolarappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'solarapp'

    def ready(self):
        import solarapp.signals  
        from django.db.utils import OperationalError
        from .models import Role

        try:
            ROLE_CHOICES = [
                ('Admin', 'Admin'),
                ('Drone controller', 'Drone controller'),
                ('Admin solar', 'Admin solar'),
                ('Data analyst', 'Data analyst'),
            ]
            for role_name, _ in ROLE_CHOICES:
                Role.objects.get_or_create(name=role_name)
        except OperationalError:
            pass

