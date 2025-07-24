
from django.apps import AppConfig

class CelicaWebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'celica_web'
    verbose_name = "CELICA-M Web Application"

    def ready(self):
        # Importer les signaux pour les connecter
        try:
            import celica_web.signals
        except ImportError:
            pass
