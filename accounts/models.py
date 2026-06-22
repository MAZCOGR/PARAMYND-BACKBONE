"""
accounts/models.py — Modèle utilisateur Paramynd Admin avec système de rôles
Copie identique de paramynd/accounts/models.py
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    SUPERADMIN = 'superadmin', 'Super Administrateur'
    ADMIN      = 'admin',      'Administrateur'
    MANAGER    = 'manager',    'Manager'
    VIEWER     = 'viewer',     'Observateur'


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.SUPERADMIN)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur Paramynd Admin — connexion par email, rôles granulaires.
    Table SQL : accounts_user
    """
    email       = models.EmailField(unique=True, verbose_name='Email')
    first_name  = models.CharField(max_length=100, blank=True, verbose_name='Prénom')
    last_name   = models.CharField(max_length=100, blank=True, verbose_name='Nom')
    role        = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        verbose_name='Rôle',
    )
    is_active   = models.BooleanField(default=True, verbose_name='Actif')
    is_staff    = models.BooleanField(default=False, verbose_name='Staff Django')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date d'inscription")
    last_login  = models.DateTimeField(null=True, blank=True, verbose_name='Dernière connexion')

    # Métadonnées additionnelles
    avatar      = models.ImageField(upload_to='avatars/', null=True, blank=True)
    notes       = models.TextField(blank=True, verbose_name='Notes internes')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.email

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]

    # --- Helpers de rôle ---
    @property
    def is_superadmin(self):
        return self.role == Role.SUPERADMIN

    @property
    def is_admin(self):
        return self.role in (Role.SUPERADMIN, Role.ADMIN)

    @property
    def is_manager(self):
        return self.role in (Role.SUPERADMIN, Role.ADMIN, Role.MANAGER)

    @property
    def role_display_badge(self):
        """Retourne une classe CSS pour le badge de rôle."""
        badges = {
            Role.SUPERADMIN: 'badge-superadmin',
            Role.ADMIN:      'badge-admin',
            Role.MANAGER:    'badge-manager',
            Role.VIEWER:     'badge-viewer',
        }
        return badges.get(self.role, 'badge-default')
