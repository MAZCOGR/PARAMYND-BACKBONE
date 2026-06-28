from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenants'
    verbose_name = 'Gestion des tenants'

    def ready(self):
        """
        Auto-remplissage du pool au démarrage de Django.

        Appelé une fois que toutes les apps sont chargées (signal AppReady).
        Lance ensure_pool_size() en background après un court délai pour laisser
        Django finir son initialisation (connexions DB, migrations, etc.).

        Actif uniquement sur Cloud Run (K_SERVICE défini) pour éviter les effets
        de bord en développement local ou lors des commandes manage.py.
        """
        import os
        import threading

        # Ne pas lancer en dev local ou lors des commandes manage.py (migrations, shell, etc.)
        # K_SERVICE est défini par Cloud Run dans l'environnement de production
        is_cloud_run = bool(os.getenv('K_SERVICE'))
        # RUN_MAIN évite le double-lancement du runserver Django en mode dev
        is_runserver_main = os.getenv('RUN_MAIN') == 'true'

        if not is_cloud_run and not is_runserver_main:
            return  # Pas en prod Cloud Run et pas en runserver → skip

        def _delayed_pool_check():
            """Attend 10s que Django finisse son démarrage, puis vérifie le pool."""
            import time
            time.sleep(10)
            try:
                from tenants.services.provisioning import ensure_pool_size
                ensure_pool_size(target_size=3)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"[POOL] Impossible de vérifier le pool au démarrage : {e}"
                )

        # Thread daemon : si le process se ferme, ce thread est tué proprement
        # (les threads ensure_pool_size() qu'il lance seront non-daemon)
        t = threading.Thread(
            target=_delayed_pool_check,
            daemon=True,
            name='pool-startup-check',
        )
        t.start()
