from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Comptes utilisateurs'

    def ready(self):
        """Auto-création / mise à jour de l'admin et nettoyage des tenants bloqués au démarrage."""
        import sys
        if 'collectstatic' in sys.argv:
            return

        def _startup_cleanup():
            try:
                # 1. Admin superuser
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

                # 2. Nettoyage des vieux tenants bloqués en statut 'deleting'
                from tenants.models import Tenant, TenantStatus
                stuck = Tenant.objects.filter(status=TenantStatus.DELETING)
                if stuck.exists():
                    deleted_count, _ = stuck.delete()
                    logger.info(f"[CLEANUP] Purged {deleted_count} stuck DELETING tenant(s) from database.")

            except Exception as e:
                logger.warning(f"[STARTUP_INIT] Startup cleanup error: {e}")

        import threading
        import time

        def _runner():
            time.sleep(3)
            _startup_cleanup()

        t = threading.Thread(target=_runner, daemon=True, name='startup-init')
        t.start()
