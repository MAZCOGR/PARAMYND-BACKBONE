from django.contrib import admin, messages as django_messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import User, Role


def force_verify_user(modeladmin, request, queryset):
    """Action admin : force email_verified + phone_verified sans passer par OTP."""
    from django.utils import timezone
    updated = queryset.update(
        email_verified=True,
        phone_verified=True,
        is_active=True,
        email_verification_code=None,
        phone_verification_code=None,
        otp_email_expires_at=None,
        otp_phone_expires_at=None,
        otp_attempts=0,
    )
    django_messages.success(request, f"{updated} utilisateur(s) forcé(s) comme vérifiés.")

force_verify_user.short_description = "✅ Forcer la vérification (bypass OTP)"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'email_verified', 'phone_verified', 'date_joined')
    list_filter = ('role', 'is_active', 'email_verified', 'phone_verified', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'otp_attempts')
    actions = [force_verify_user]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Rôle & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Vérification OTP', {'fields': (
            'email_verified', 'email_verification_code', 'otp_email_expires_at',
            'phone_verified', 'phone_verification_code', 'otp_phone_expires_at',
            'otp_attempts',
        )}),
        ('Notes', {'fields': ('notes',)}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )
