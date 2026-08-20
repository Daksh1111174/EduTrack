import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create the initial EduTrack admin user if it does not exist."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_ADMIN_USERNAME")
        email = os.environ.get("DJANGO_ADMIN_EMAIL")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Admin environment variables are not configured. "
                    "Skipping admin creation."
                )
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin user '{username}' already exists."
                )
            )
            return

        user = User.objects.create_superuser(
            username=username,
            email=email or "",
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{user.username}' created successfully."
            )
        )
