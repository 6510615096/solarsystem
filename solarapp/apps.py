from django.apps import AppConfig

class SolarappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'solarapp'

    def ready(self):
        import solarapp.signals  