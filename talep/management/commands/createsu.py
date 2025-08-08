# talep/management/commands/createsu.py
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create/update superuser from env vars"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SU_USERNAME", "admin")
        password = os.environ.get("DJANGO_SU_PASSWORD", "YeniSifre!123")
        email    = os.environ.get("DJANGO_SU_EMAIL", "admin@example.com")

        if not username or not password:
            self.stdout.write("createsu skipped: missing DJANGO_SU_USERNAME or DJANGO_SU_PASSWORD")
            return

        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email}
        )
        user.is_staff = True
        user.is_superuser = True
        user.email = email or user.email
        user.set_password(password)
        user.save()

        msg = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' {msg}."))
