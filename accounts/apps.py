from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Comptes utilisateurs'

    def ready(self):
        """Auto-création / mise à jour de l'admin au démarrage."""
        import sys
        # Ne pas exécuter pendant les commandes de build collectstatic etc.
        if 'collectstatic' in sys.argv:
            return

        def _ensure_admin():
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user, created = User.objects.get_or_create(
                    email='admin@ripanna.com',
                    defaults={
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                    }
                )
                user.set_password('Admin123!')
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save()
                logger.info("[AUTH_INIT] Admin user admin@ripanna.com ready.")
            except Exception as e:
                logger.warning(f"[AUTH_INIT] Could not auto-ensure admin user: {e}")

        # Lancer au démarrage (avec délai court pour laisser les DB ready)
        import threading
        import time

        def _runner():
            time.sleep(2)
            _ensure_admin()

        t = threading.Thread(target=_runner, daemon=True, name='admin-init')
        t.start()
