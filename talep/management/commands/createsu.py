import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Create a superuser if it doesn't exist (reads creds from env)"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SU_USERNAME", "admin")
        password = os.environ.get("DJANGO_SU_PASSWORD", "admin123")
        email = os.environ.get("DJANGO_SU_EMAIL", "admin@example.com")

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write("Superuser already exists.")
