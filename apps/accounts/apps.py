# apps/accounts/apps.py
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Accounts"

    def ready(self) -> None:
        # Auto-create API token for every new user
        from django.db.models.signals import post_save
        from django.contrib.auth import get_user_model
        from rest_framework.authtoken.models import Token

        def create_auth_token(sender, instance, created, **kwargs):
            if created:
                Token.objects.get_or_create(user=instance)

        post_save.connect(create_auth_token, sender=get_user_model(), weak=False)
