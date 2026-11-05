from django.apps import AppConfig


class ClinicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clinic"

    def ready(self):
        from django.db.models.signals import post_migrate
        from .signals import create_roles
        post_migrate.connect(create_roles, sender=self, dispatch_uid="clinic.create_roles")
