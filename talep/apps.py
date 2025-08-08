# talep/apps.py
from django.apps import AppConfig
import os

class TalepConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'talep'

    def ready(self):
        # İstersen kapatmak için AUTO_CREATE_SU=0 yaparsın
        if os.environ.get("AUTO_CREATE_SU", "1") != "1":
            return

        from django.contrib.auth import get_user_model
        from django.db.utils import OperationalError, ProgrammingError

        username = os.environ.get("DJANGO_SU_USERNAME", "admin")
        password = os.environ.get("DJANGO_SU_PASSWORD", "admin123")
        email = os.environ.get("DJANGO_SU_EMAIL", "admin@example.com")

        try:
            User = get_user_model()
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "is_staff": True, "is_superuser": True},
            )
            # Her start'ta şifreyi ENV'deki değere ayarla
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.email = email
            user.save()
        except (OperationalError, ProgrammingError):
            # migrate bitmeden çağrılırsa sessiz geç
            pass
