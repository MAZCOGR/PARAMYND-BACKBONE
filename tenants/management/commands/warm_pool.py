"""
tenants/management/commands/warm_pool.py

Commande Django pour gérer le pool de tenants pré-provisionnés.

Usage :
    python manage.py warm_pool              → Remplit le pool jusqu'à 3 tenants
    python manage.py warm_pool --count 5    → Remplit jusqu'à 5 tenants
    python manage.py warm_pool --status     → Affiche l'état du pool sans rien créer
    python manage.py warm_pool --force 2    → Force la création de 2 tenants de pool
                                              (même si le pool est déjà plein)

Peut être appelé :
    - Manuellement depuis le terminal
    - Via un Cloud Run Job planifié (Cloud Scheduler, toutes les heures)
    - Via la vue admin /tenants/pool/refill/
"""
import threading
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Gestion du pool de tenants pré-provisionnés (Warm Pool)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help="Taille cible du pool (défaut: 3). Le pool sera rempli jusqu'à ce nombre.",
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help="Afficher l'état actuel du pool sans créer de tenants.",
        )
        parser.add_argument(
            '--force',
            type=int,
            default=0,
            metavar='N',
            help="Forcer la création de N tenants de pool supplémentaires, peu importe la taille actuelle.",
        )
        parser.add_argument(
            '--no-wait',
            action='store_true',
            help="Lancer les provisioning en background et revenir immédiatement (défaut: attendre la fin).",
        )

    def handle(self, *args, **options):
        from tenants.models import Tenant, TenantStatus
        from tenants.services.provisioning import provision_pool_tenant, ensure_pool_size

        target = options['count']
        force = options['force']
        show_status = options['status']
        no_wait = options['no_wait']

        # -- Affichage du statut -----------------------------------------------
        pooled = Tenant.objects.filter(status=TenantStatus.POOLED, is_pool_tenant=True)
        provisioning = Tenant.objects.filter(status=TenantStatus.PROVISIONING, is_pool_tenant=True)
        failed = Tenant.objects.filter(status=TenantStatus.FAILED, is_pool_tenant=True)

        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.HTTP_INFO("  WARM POOL -- Etat actuel"))
        self.stdout.write("-" * 60)
        self.stdout.write(
            f"  [OK]  Prets (POOLED)          : {self.style.SUCCESS(str(pooled.count()))}"
        )
        self.stdout.write(
            f"  [>>]  En provisioning         : {self.style.WARNING(str(provisioning.count()))}"
        )
        self.stdout.write(
            f"  [!!]  Echoues                 : {self.style.ERROR(str(failed.count()))}"
        )
        self.stdout.write(f"  [>>]  Taille cible            : {target}")
        self.stdout.write("-" * 60)

        if pooled.exists():
            self.stdout.write("\n  Tenants de pool disponibles :")
            for t in pooled.order_by('pool_created_at'):
                age = timezone.now() - t.pool_created_at if t.pool_created_at else None
                age_str = f"{int(age.total_seconds() / 60)} min" if age else "?"
                self.stdout.write(
                    f"    * {self.style.SUCCESS(t.slug):30s}  "
                    f"cree il y a {age_str}  "
                    f"[{t.cloud_run_url or 'URL inconnue'}]"
                )

        if failed.exists():
            self.stdout.write(f"\n  {self.style.ERROR('Tenants de pool en erreur :')} ")
            for t in failed.order_by('-updated_at'):
                self.stdout.write(f"    x {self.style.ERROR(t.slug)}  (etape: {t.provisioning_step})")
            self.stdout.write(
                f"\n  {self.style.WARNING('Astuce :')} Supprimez les tenants FAILED avec "
                "'python manage.py shell' -> "
                "Tenant.objects.filter(is_pool_tenant=True, status='failed').delete()"
            )

        self.stdout.write("")

        if show_status:
            return  # Mode --status : juste afficher, ne pas créer

        # -- Forçage de N créations supplémentaires ----------------------------
        if force > 0:
            self.stdout.write(
                f"  [!!] Forçage de {force} creation(s) de pool (--force)..."
            )
            threads = []
            for i in range(force):
                t = threading.Thread(
                    target=provision_pool_tenant,
                    daemon=False,
                    name=f'warm-pool-force-{i}',
                )
                t.start()
                threads.append(t)
                self.stdout.write(f"    -> Thread {i + 1}/{force} lance")

            if not no_wait:
                self.stdout.write("  Attente de la fin des provisioning...")
                for t in threads:
                    t.join()
                self.stdout.write(self.style.SUCCESS("  [OK] Provisioning termine !"))
            else:
                self.stdout.write(
                    self.style.WARNING("  Retour immediat (--no-wait). Verifiez le statut dans quelques minutes.")
                )
            return

        # -- Remplissage automatique jusqu'à target ----------------------------
        total_in_pool = pooled.count() + provisioning.count()
        missing = target - total_in_pool

        if missing <= 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] Pool deja plein ({pooled.count()} prets + {provisioning.count()} en cours, target={target}). Rien a faire."
                )
            )
            return

        self.stdout.write(
            f"  [>>] Lancement de {missing} provisioning(s) de pool "
            f"(actuellement: {total_in_pool}/{target})..."
        )

        threads = []
        for i in range(missing):
            t = threading.Thread(
                target=provision_pool_tenant,
                daemon=False,
                name=f'warm-pool-{i}',
            )
            t.start()
            threads.append(t)
            self.stdout.write(f"    -> Thread {i + 1}/{missing} lance")

        if not no_wait:
            self.stdout.write("\n  Attente de la fin des provisioning (~7-10 min)...")
            for t in threads:
                t.join()

            # Afficher le résultat final
            pooled_after = Tenant.objects.filter(status=TenantStatus.POOLED, is_pool_tenant=True).count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n  [OK] Termine ! Pool actuel : {pooled_after} tenant(s) pret(s)."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\n  Retour immediat (--no-wait). "
                    f"Utilisez 'python manage.py warm_pool --status' pour suivre la progression."
                )
            )
