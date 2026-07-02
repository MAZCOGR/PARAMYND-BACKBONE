"""
accounts/management/commands/verify_user.py
Force la vérification OTP d'un utilisateur par email (bypass admin).
Usage: python manage.py verify_user praks275@gmail.com
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Force la vérification email+phone d\'un utilisateur (bypass OTP)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email de l\'utilisateur')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Utilisateur {email} introuvable.'))
            return

        self.stdout.write(f'Utilisateur trouvé : {user.email}')
        self.stdout.write(f'  is_active avant    : {user.is_active}')
        self.stdout.write(f'  email_verified     : {user.email_verified}')
        self.stdout.write(f'  phone_verified     : {user.phone_verified}')
        self.stdout.write(f'  email OTP          : {user.email_verification_code}')
        self.stdout.write(f'  phone OTP          : {user.phone_verification_code}')

        user.email_verified = True
        user.phone_verified = True
        user.is_active = True
        user.email_verification_code = None
        user.phone_verification_code = None
        user.otp_email_expires_at = None
        user.otp_phone_expires_at = None
        user.otp_attempts = 0
        user.save(update_fields=[
            'email_verified', 'phone_verified', 'is_active',
            'email_verification_code', 'phone_verification_code',
            'otp_email_expires_at', 'otp_phone_expires_at', 'otp_attempts',
        ])

        self.stdout.write(self.style.SUCCESS(
            f'✅ {email} vérifié et activé avec succès.'
        ))
