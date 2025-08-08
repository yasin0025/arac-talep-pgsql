# talep/apps.py
from django.apps import AppConfig
import os

class TalepConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'talep'

    def ready(self):
        # İstersen kapatmak için AUTO_CREATE_SU=0 yap
        if os.environ.get("AUTO_CREATE_SU", "1") != "1":
            return

        # DB hazır mı, auth_user var mı? Değilse hiç dokunma.
        try:
            from django.db import connection
            tables = connection.introspection.table_names()
            if 'auth_user' not in tables:
                return
        except Exception:
            return  # DB bağlantısı hazır değilse sessizce çık

        from django.contrib.auth import get_user_model

        username = os.environ.get("DJANGO_SU_USERNAME", "admin")
        password = os.environ.get("DJANGO_SU_PASSWORD", "admin123")
        email = os.environ.get("DJANGO_SU_EMAIL", "admin@example.com")

        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        # Her açılışta şifreyi ENV'deki değere sabitle (giriş sorununu kökten çözsün)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.email = email
        user.save()
