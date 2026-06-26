"""
tenants/management/commands/create_tenant_superuser.py

C-03 fix : Commande de gestion sécurisée pour créer le superuser d'un tenant.
Lit le mot de passe depuis la variable d'env DJANGO_SUPERUSER_PASSWORD
(positionnée par Cloud Run via --set-env-vars, pas interpolée dans du code Python).

Usage (Cloud Run Job) :
    python manage.py create_tenant_superuser \
        --email=admin@tenant.com \
        --noinput

Le mot de passe est lu depuis os.environ['DJANGO_SUPERUSER_PASSWORD'].
"""
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Crée le superuser initial pour un tenant. Lit le password depuis DJANGO_SUPERUSER_PASSWORD."

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help="Email du superuser à créer.")
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_true',
            dest='noinput',
            help="Ne pas demander de confirmation interactive.",
        )

    def handle(self, *args, **options):
        email = options['email'].strip().lower()

        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not password:
            raise CommandError(
                "La variable d'environnement DJANGO_SUPERUSER_PASSWORD est requise."
            )

        if len(password) < 8:
            raise CommandError("Le mot de passe doit contenir au moins 8 caractères.")

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"L'utilisateur {email} existe déjà — aucune action.")
            )
            return

        try:
            User.objects.create_superuser(
                email=email,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superuser {email} créé avec succès.")
            )
        except Exception as e:
            raise CommandError(f"Erreur lors de la création du superuser : {e}")
