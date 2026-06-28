"""
tenants/services/provisioning.py
Service de provisioning automatique complet pour un nouveau tenant client.

Flow :
  1. Créer la base PostgreSQL dans Cloud SQL
  2. Déployer le service Cloud Run avec la dernière image disponible
  3. Exécuter les migrations Django via Cloud Run Job
  4. Créer le compte superuser admin du client via Cloud Run Job
  5. Mettre à jour le statut du tenant → ACTIVE

Appelé en thread background depuis core/views.py après validation OTP.
"""
import logging
import subprocess
import time
from typing import Optional

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Constantes GCP
DEFAULT_PROJECT   = getattr(settings, 'GCP_PROJECT_ID', 'yellow-455523')
DEFAULT_REGION    = getattr(settings, 'GCP_REGION', 'europe-west9')
DEFAULT_SQL_INST  = getattr(settings, 'CLOUD_SQL_INSTANCE', 'yellow-455523:europe-west9:yellow-db-paris')
DEFAULT_IMAGE_TAG = 'latest'


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNES
# ──────────────────────────────────────────────────────────────────────────────

def _log(tenant_slug: str, step: str, msg: str, error: bool = False):
    """Log structuré avec préfixe tenant."""
    fn = logger.error if error else logger.info
    fn(f"[PROVISION:{tenant_slug}] [{step}] {msg}")


def _sanitize_cmd_for_log(args: list) -> list:
    """
    C-02 fix : masque les valeurs sensibles dans les arguments gcloud avant logging.
    Remplace les valeurs après DJANGO_SUPERUSER_PASSWORD= par '***'.
    """
    sanitized = []
    for arg in args:
        if 'DJANGO_SUPERUSER_PASSWORD=' in arg:
            # Masquer uniquement la valeur du password dans --set-env-vars
            import re
            arg = re.sub(r'(DJANGO_SUPERUSER_PASSWORD=)[^,\s]+', r'\1***', arg)
        sanitized.append(arg)
    return sanitized


def _run_gcloud(args: list, tenant_slug: str, step: str, timeout: int = 300) -> tuple[bool, str]:
    """
    Exécute une commande gcloud et retourne (success, output).
    C-02 fix : les arguments sont sanitizés avant logging (pas de secrets en clair).
    """
    cmd = ['gcloud'] + args + ['--quiet']
    # C-02 fix : logger la version sanitizée (password masqué)
    safe_cmd = _sanitize_cmd_for_log(cmd)
    _log(tenant_slug, step, f"Running: {' '.join(safe_cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            _log(tenant_slug, step, f"FAILED (code {result.returncode}): {output}", error=True)
            return False, output
        _log(tenant_slug, step, f"OK: {output[:200]}")
        return True, output
    except subprocess.TimeoutExpired:
        msg = f"Timeout after {timeout}s"
        _log(tenant_slug, step, msg, error=True)
        return False, msg
    except Exception as e:
        _log(tenant_slug, step, f"Exception: {e}", error=True)
        return False, str(e)


def _get_latest_image_uri(project: str = DEFAULT_PROJECT, region: str = DEFAULT_REGION) -> str:
    """
    Retourne l'URI de la dernière image disponible dans Artifact Registry.
    Utilise le tag 'latest' en priorité.
    """
    try:
        from tenants.services.artifact_registry import get_image_uri
        return get_image_uri(DEFAULT_IMAGE_TAG)
    except Exception as e:
        logger.warning(f"Artifact Registry unavailable: {e} — using hardcoded latest")
        repo   = getattr(settings, 'ARTIFACT_REGISTRY_REPO', 'paramynd')
        image  = getattr(settings, 'PARAMYND_IMAGE_NAME', 'app')
        return f"{region}-docker.pkg.dev/{project}/{repo}/{image}:{DEFAULT_IMAGE_TAG}"


# ──────────────────────────────────────────────────────────────────────────────
# ÉTAPES DU PROVISIONING
# ──────────────────────────────────────────────────────────────────────────────

def step_create_database(tenant_slug: str, db_name: str, project: str) -> bool:
    """
    Étape 1 — Crée la base PostgreSQL dans Cloud SQL.
    Si la base existe déjà (tenant supprimé puis recréé avec le même slug),
    on la supprime et recrée proprement pour éviter les conflits de migrations Django.
    """
    step = 'DB_CREATE'
    _log(tenant_slug, step, f"Creating database '{db_name}' on instance yellow-db-paris...")

    ok, out = _run_gcloud([
        'sql', 'databases', 'create', db_name,
        '--instance=yellow-db-paris',
        f'--project={project}',
        '--charset=UTF8',
        '--collation=en_US.UTF8',
    ], tenant_slug, step, timeout=60)

    if not ok:
        if 'already exists' in out.lower() or 'duplicate' in out.lower():
            # La base existe déjà (tenant supprimé puis recréé avec le même slug).
            # On la supprime et recrée proprement pour éviter les conflits
            # de schéma Django (tables django_migrations obsolètes, etc.).
            _log(tenant_slug, step,
                 f"Database '{db_name}' already exists — dropping and recreating for a clean state...")

            drop_ok, drop_out = _run_gcloud([
                'sql', 'databases', 'delete', db_name,
                '--instance=yellow-db-paris',
                f'--project={project}',
            ], tenant_slug, step, timeout=60)

            if not drop_ok:
                _log(tenant_slug, step,
                     f"Failed to drop existing database '{db_name}': {drop_out}", error=True)
                return False

            # Petite pause pour laisser Cloud SQL libérer les ressources
            time.sleep(3)

            # Recréer la base
            recreate_ok, recreate_out = _run_gcloud([
                'sql', 'databases', 'create', db_name,
                '--instance=yellow-db-paris',
                f'--project={project}',
                '--charset=UTF8',
                '--collation=en_US.UTF8',
            ], tenant_slug, step, timeout=60)

            if not recreate_ok:
                _log(tenant_slug, step,
                     f"Failed to recreate database '{db_name}': {recreate_out}", error=True)
                return False

            _log(tenant_slug, step, f"Database '{db_name}' dropped and recreated successfully.")
            return True
        return False
    return True


def step_deploy_cloud_run(tenant_slug: str, db_name: str, project: str, region: str,
                           cloud_sql_instance: str, image_uri: str, env_vars: dict = None) -> tuple[bool, str]:
    """
    Étape 2 — Déploie le service Cloud Run pour le tenant.
    Retourne (success, service_url).
    """
    step = 'CR_DEPLOY'
    _log(tenant_slug, step, f"Deploying Cloud Run service '{tenant_slug}' with image {image_uri}...")

    from tenants.services.cloud_run import deploy_service
    result = deploy_service(
        tenant_slug=tenant_slug,
        image_uri=image_uri,
        gcp_project_id=project,
        region=region,
        cloud_sql_instance=cloud_sql_instance,
        db_name=db_name,
        min_instances=0,
        max_instances=10,
        memory='512Mi',
        cpu='1',
        env_vars=env_vars,
    )

    if not result.get('success'):
        _log(tenant_slug, step, f"FAILED: {result.get('error')}", error=True)
        return False, ''

    url = result.get('url', f'https://{tenant_slug}-{project.split("-")[0]}.{region}.run.app')
    _log(tenant_slug, step, f"Service deployed at: {url}")
    return True, url


def step_run_migrations(tenant_slug: str, db_name: str, project: str, region: str,
                         cloud_sql_instance: str, image_uri: str) -> bool:
    """
    Étape 3 — Lance les migrations Django via Cloud Run Job.
    """
    step = 'MIGRATE'
    job_name = f'{tenant_slug}-migrate'
    _log(tenant_slug, step, f"Creating migration job '{job_name}'...")

    # Supprimer le job s'il existe déjà (peut rester d'un provisioning précédent
    # avec le même slug si le tenant a été supprimé et recréé).
    _run_gcloud([
        'run', 'jobs', 'delete', job_name,
        f'--region={region}', f'--project={project}',
    ], tenant_slug, step, timeout=60)

    # Créer le job
    ok, out = _run_gcloud([
        'run', 'jobs', 'create', job_name,
        f'--image={image_uri}',
        f'--region={region}',
        f'--project={project}',
        f'--set-cloudsql-instances={cloud_sql_instance}',
        f'--set-env-vars=DJANGO_SETTINGS_MODULE=core.settings,DB_NAME={db_name},DB_USER=admin,CLOUD_SQL_INSTANCE={cloud_sql_instance}',
        '--set-secrets=DB_PASSWORD=DB_PASS:latest,SECRET_KEY=PARAMYND_SECRET_KEY:latest,JWT_SIGNING_KEY=PARAMYND_JWT_SIGNING_KEY:latest',
        '--command=python',
        '--args=manage.py,migrate',
        '--max-retries=1',
    ], tenant_slug, step, timeout=120)  # BUG-D06 fix : 60s → 120s

    if not ok:
        return False

    # Exécuter le job
    _log(tenant_slug, step, "Executing migration job...")
    ok, out = _run_gcloud([
        'run', 'jobs', 'execute', job_name,
        f'--region={region}',
        f'--project={project}',
        '--wait',
    ], tenant_slug, step, timeout=300)

    return ok


def step_create_superuser(tenant_slug: str, db_name: str, project: str, region: str,
                           cloud_sql_instance: str, image_uri: str,
                           admin_email: str, admin_password: str) -> bool:
    """
    Étape 4 — Crée le compte superuser admin du client dans la DB du tenant.
    Utilise un Cloud Run Job avec les credentials passés en variables d'env.

    C-03 fix : la voie de secours avec interpolation directe du password dans
    un script Python shell a été supprimée (risque d'injection).
    En cas d'échec, le tenant reste actif mais sans compte superuser initial.
    L'utilisateur peut créer son compte via le lien 'Mot de passe oublié'.
    """
    step = 'SUPERUSER'
    job_name = f'{tenant_slug}-superuser'
    _log(tenant_slug, step, f"Creating admin account for {admin_email}...")

    # Supprimer le job s'il existe déjà
    _run_gcloud([
        'run', 'jobs', 'delete', job_name,
        f'--region={region}', f'--project={project}',
    ], tenant_slug, step, timeout=30)

    # Créer le job — le password est passé via DJANGO_SUPERUSER_PASSWORD
    # C-02 fix : le logging est sanitizé par _sanitize_cmd_for_log()
    ok, out = _run_gcloud([
        'run', 'jobs', 'create', job_name,
        f'--image={image_uri}',
        f'--region={region}',
        f'--project={project}',
        f'--set-cloudsql-instances={cloud_sql_instance}',
        (
            f'--set-env-vars=DJANGO_SETTINGS_MODULE=core.settings,'
            f'DB_NAME={db_name},'
            f'DB_USER=admin,'
            f'CLOUD_SQL_INSTANCE={cloud_sql_instance},'
            f'DJANGO_SUPERUSER_EMAIL={admin_email},'
            f'DJANGO_SUPERUSER_PASSWORD={admin_password},'
            f'DJANGO_SUPERUSER_USERNAME={admin_email}'
        ),
        '--set-secrets=DB_PASSWORD=DB_PASS:latest,SECRET_KEY=PARAMYND_SECRET_KEY:latest,JWT_SIGNING_KEY=PARAMYND_JWT_SIGNING_KEY:latest',
        '--command=python',
        # BUG-D01 fix : utilise la commande custom create_tenant_superuser
        # qui sait gérer accounts.User (email comme identifiant unique).
        # createsuperuser vanilla Django échoue sur ce modèle custom.
        '--args=manage.py,create_tenant_superuser,--email,' + admin_email + ',--noinput',
        '--max-retries=1',
    ], tenant_slug, step, timeout=120)  # BUG-D06 fix : 60s → 120s (GCP peut être lent)

    if not ok:
        # C-03 fix : la voie de secours avec shell -c a été supprimée.
        # Elle était vulnérable à l'injection Python si le password contenait
        # des apostrophes ou des caractères spéciaux.
        _log(tenant_slug, step, "Could not create superuser job — tenant will still be active.", error=True)
        return False

    # Exécuter le job
    _log(tenant_slug, step, "Executing superuser creation job...")
    ok, out = _run_gcloud([
        'run', 'jobs', 'execute', job_name,
        f'--region={region}',
        f'--project={project}',
        '--wait',
    ], tenant_slug, step, timeout=240)  # BUG-D06 fix : 180s → 240s

    if not ok:
        _log(tenant_slug, step, "Superuser job failed — tenant will still be active.", error=True)
        return False

    _log(tenant_slug, step, f"Admin account created for {admin_email} ✅")
    return True

def step_create_oauth_app(tenant, admin_email: str) -> tuple[str, str]:
    """
    Crée une application OAuth2 First-Party pour ce tenant sans configurer les URLs (fait après).
    Client PUBLIC + PKCE : le code challenge est obligatoire côté serveur (PKCE_REQUIRED=True),
    et USE_PKCE=True dans le backend social-auth côté tenant.
    """
    from oauth2_provider.models import Application
    from django.contrib.auth import get_user_model
    import secrets

    User = get_user_model()
    user = User.objects.filter(email=admin_email).first()

    client_id = secrets.token_urlsafe(32)
    client_secret = secrets.token_urlsafe(64)

    app, created = Application.objects.get_or_create(
        name=f"SSO-{tenant.slug}",
        defaults={
            'user': user,
            'client_id': client_id,
            'client_secret': client_secret,
            'client_type': Application.CLIENT_PUBLIC,   # PUBLIC requis pour PKCE
            'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
            'skip_authorization': True,
        }
    )
    if not created:
        client_id = app.client_id
        # Migrer les apps existantes vers PUBLIC si nécessaire
        update_fields = []
        if app.client_type != Application.CLIENT_PUBLIC:
            app.client_type = Application.CLIENT_PUBLIC
            update_fields.append('client_type')
        # Régénérer le secret (le hashed en DB ne peut pas être relu)
        client_secret = secrets.token_urlsafe(64)
        app.client_secret = client_secret
        update_fields.append('client_secret')
        app.save(update_fields=update_fields)

    return client_id, client_secret


def step_update_oauth_app_urls(tenant):
    """Met à jour les URIs de redirection de l'application OAuth2."""
    from oauth2_provider.models import Application
    app = Application.objects.filter(name=f"SSO-{tenant.slug}").first()
    if app:
        uris = []
        # URL Cloud Run directe (interne)
        if tenant.cloud_run_url:
            uris.append(f"{tenant.cloud_run_url}/social-auth/complete/paramynd-admin/")
        # URL wildcard paramynd.com (via Load Balancer) — toujours présente
        uris.append(f"https://{tenant.slug}.paramynd.com/social-auth/complete/paramynd-admin/")
        # URL Cloud Run alternative (format region)
        project = tenant.gcp_project_id or 'yellow-455523'
        region = tenant.cloud_run_region or 'europe-west9'
        uris.append(f"https://{tenant.slug}-{project.replace('-', '')[:12]}.{region}.run.app/social-auth/complete/paramynd-admin/")
        # Domaine personnalisé si actif
        if tenant.custom_domain and tenant.domain_status == 'active':
            uris.append(f"https://{tenant.custom_domain}/social-auth/complete/paramynd-admin/")

        app.redirect_uris = " ".join(uris)
        app.save(update_fields=['redirect_uris'])




# ──────────────────────────────────────────────────────────────────────────────
# WARM POOL — GESTION DU POOL DE TENANTS PRÉ-PROVISIONNÉS
# ──────────────────────────────────────────────────────────────────────────────

def get_available_pool_tenant():
    """
    Retourne le premier tenant de pool disponible (status=POOLED, is_pool_tenant=True).

    Utilise select_for_update(skip_locked=True) pour garantir qu'un seul thread
    peut réserver un tenant de pool à la fois, même en cas d'inscriptions simultanées.

    Retourne None si le pool est vide.
    """
    from tenants.models import Tenant, TenantStatus
    from django.db import transaction

    with transaction.atomic():
        tenant = (
            Tenant.objects
            .select_for_update(skip_locked=True)
            .filter(status=TenantStatus.POOLED, is_pool_tenant=True)
            .order_by('pool_created_at')  # FIFO : utiliser les plus anciens en premier
            .first()
        )
        if tenant:
            # Pré-réserver le tenant en le passant en PROVISIONING
            # pour éviter qu'un autre thread le prenne pendant l'assignation
            tenant.status = TenantStatus.PROVISIONING
            tenant.save(update_fields=['status', 'updated_at'])
        return tenant



def _cleanup_pool_cloud_run_service(pool_slug: str, project: str, region: str):
    """
    Supprime le service Cloud Run du pool apres assignation au client.

    Le service pool-abc123 est devenu inutile une fois qu'un nouveau service
    avec le vrai slug client a ete deploye. On le supprime pour eviter des
    couts GCP inutiles et garder le projet propre.

    Appele en thread daemon — les erreurs sont loguees mais n'affectent pas
    l'activation du tenant client.
    """
    import time
    # Attendre 60s que le nouveau service client soit bien stable avant de supprimer
    time.sleep(60)
    _log(pool_slug, 'POOL:CLEANUP', f"Suppression du service Cloud Run pool '{pool_slug}'...")
    ok, out = _run_gcloud([
        'run', 'services', 'delete', pool_slug,
        f'--region={region}',
        f'--project={project}',
        '--quiet',
    ], pool_slug, 'POOL:CLEANUP', timeout=120)
    if ok:
        _log(pool_slug, 'POOL:CLEANUP', f"Service pool '{pool_slug}' supprime avec succes.")
    else:
        # Non bloquant : si la suppression echoue, le service restera inactif
        # (scale-to-zero) et pourra etre supprime manuellement.
        logger.warning(f"[POOL:CLEANUP] Echec suppression service '{pool_slug}': {out}")


def assign_pool_tenant(pool_tenant_id: str, client_slug: str, company: str,
                       admin_email: str, admin_password: str):
    """
    Assigne un tenant de pool pre-provisionne a un vrai client.

    CORRECTION URL MASK : Le NEG GCP utilise urlMask='<service>.paramynd.com',
    ce qui signifie que acme.paramynd.com doit pointer vers un Cloud Run service
    nomme exactement 'acme'. On NE PEUT PAS juste renommer le service pool-abc123.

    Ce que cette fonction fait :
        1. Creer l'app OAuth2 pour le vrai client
        2. Deployer un NOUVEAU Cloud Run service avec le slug client (ex: 'acme')
           en reutilisant la BDD deja migree du pool tenant (gain ~3-5 min)
        3. Creer le superuser client
        4. Mettre a jour le record Tenant (slug, nom, email, statut)
        5. Supprimer le service Cloud Run pool en background (nettoyage)

    Temps gagne vs provision classique :
        - DB creation (~60s)     : economisee (deja faite dans le pool)
        - Migrations (~2-3 min)  : economisees (deja faites dans le pool)
        - CR deploy client slug  : ~2-3 min (necessaire a cause du URL mask)
        - Superuser              : ~1-2 min
        Total : ~3-5 min (vs 7-10 min sans pool) = gain 40-50%

    Args:
        pool_tenant_id  : UUID du tenant de pool (deja reserve en PROVISIONING)
        client_slug     : Slug final du client (ex: 'acme-corp')
        company         : Nom de l'entreprise du client
        admin_email     : Email du compte admin client
        admin_password  : Mot de passe temporaire pour le superuser
    """
    from tenants.models import Tenant, TenantStatus, DomainStatus, Deployment, DeploymentStatus

    try:
        tenant = Tenant.objects.get(id=pool_tenant_id)
    except Tenant.DoesNotExist:
        logger.error(f"[POOL:ASSIGN] Tenant de pool {pool_tenant_id} introuvable en DB")
        return

    pool_slug = tenant.slug           # ex: pool-a3f8c2
    pool_db_name = tenant.db_name     # ex: pool_a3f8c2 — BDD deja migree, on la reutilise
    project = tenant.gcp_project_id or DEFAULT_PROJECT
    region = tenant.cloud_run_region or DEFAULT_REGION
    cloud_sql_instance = tenant.cloud_sql_instance or DEFAULT_SQL_INST
    image_uri = _get_latest_image_uri(project, region)
    image_tag = image_uri.split(':')[-1]
    public_domain = f"{client_slug}.paramynd.com"

    _log(client_slug, 'POOL:ASSIGN',
         f"Assignation pool '{pool_slug}' (DB: {pool_db_name}) -> client '{client_slug}' ({admin_email})")

    # Mettre a jour le slug et email pour le suivi pendant l'assignation
    tenant.contact_email = admin_email
    tenant.save(update_fields=['contact_email', 'updated_at'])

    deployment = Deployment.objects.create(
        tenant=tenant,
        image_tag=image_tag,
        image_uri=image_uri,
        status=DeploymentStatus.IN_PROGRESS,
        deployed_by='pool-assign',
    )

    # ── Etape 1 : Creer l'app OAuth2 pour le vrai client ─────────────────────
    tenant.provisioning_step = 'oauth_setup'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    client_id, client_secret = step_create_oauth_app(tenant, admin_email)

    # ── Etape 2 : Deployer un NOUVEAU Cloud Run service avec le vrai slug ─────
    # CRITIQUE : Le NEG urlMask='<service>.paramynd.com' exige que le nom du
    # service Cloud Run soit exactement le slug client. On reutilise la BDD du pool.
    tenant.provisioning_step = 'cr_deploy'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    _log(client_slug, 'POOL:CR_DEPLOY',
         f"Deploiement Cloud Run '{client_slug}' (reutilise DB pool: {pool_db_name})")

    from django.conf import settings as django_settings
    extra_env = {
        'PUBLIC_DOMAIN': public_domain,
        'SOCIAL_AUTH_PARAMYND_ADMIN_KEY': client_id,
        'SOCIAL_AUTH_PARAMYND_ADMIN_SECRET': client_secret,
        'PARAMYND_ADMIN_URL': getattr(django_settings, 'PARAMYND_ADMIN_URL', 'https://paramynd.com'),
    }

    ok, service_url = step_deploy_cloud_run(
        client_slug,        # nom du nouveau service = slug client
        pool_db_name,       # reutilise la BDD deja migree du pool
        project, region, cloud_sql_instance, image_uri,
        env_vars=extra_env,
    )

    if not ok:
        _log(client_slug, 'POOL:CR_DEPLOY', 'Echec deploiement Cloud Run client', error=True)
        _mark_failed(tenant, deployment, 'Echec deploiement Cloud Run (pool assign)')
        return

    # ── Etape 3 : Creer le superuser client ───────────────────────────────────
    tenant.provisioning_step = 'superuser'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    step_create_superuser(
        client_slug, pool_db_name,
        project, region, cloud_sql_instance, image_uri,
        admin_email, admin_password
    )

    # ── Etape 4 : Finaliser le record Tenant ──────────────────────────────────
    from django.utils import timezone as tz
    tenant.name = company
    tenant.slug = client_slug                    # le slug devient celui du client
    tenant.contact_email = admin_email
    tenant.custom_domain = public_domain
    tenant.domain_status = DomainStatus.ACTIVE
    tenant.cloud_run_url = service_url
    tenant.cloud_run_service_name = client_slug  # service Cloud Run = slug client
    tenant.current_image_tag = image_tag
    tenant.is_pool_tenant = False
    tenant.pool_created_at = None
    tenant.provisioning_step = 'done'
    tenant.status = TenantStatus.ACTIVE
    tenant.last_deployed_at = tz.now()
    tenant.save(update_fields=[
        'name', 'slug', 'contact_email', 'custom_domain', 'domain_status',
        'cloud_run_url', 'cloud_run_service_name', 'current_image_tag',
        'is_pool_tenant', 'pool_created_at', 'provisioning_step',
        'status', 'last_deployed_at', 'updated_at',
    ])

    deployment.status = DeploymentStatus.SUCCESS
    deployment.completed_at = tz.now()
    deployment.save(update_fields=['status', 'completed_at'])

    # Mettre a jour les redirect URIs OAuth2 avec le vrai domaine
    step_update_oauth_app_urls(tenant)

    _log(client_slug, 'POOL:DONE',
         f"[OK] Pool assign complete : '{client_slug}' actif sur https://{public_domain}")

    # ── Etape 5 (async) : Supprimer le service Cloud Run pool devenu inutile ──
    # Le service 'pool-abc123' ne sert plus — on le supprime en background
    # pour ne pas bloquer l'activation du tenant client.
    import threading
    threading.Thread(
        target=_cleanup_pool_cloud_run_service,
        args=(pool_slug, project, region),
        daemon=True,
        name=f'pool-cleanup-{pool_slug}',
    ).start()



def provision_pool_tenant():
    """
    Crée et provisionne un nouveau tenant de pool (réserve).

    Ce tenant aura un slug temporaire de type 'pool-{uuid}' et passera par
    toutes les étapes normales (DB + Cloud Run + migrations) SAUF la création
    du superuser (elle sera faite à l'assignation client).

    Doit être appelé en thread background.
    """
    import uuid as _uuid
    from django.utils import timezone as tz
    from tenants.models import Tenant, TenantStatus, Deployment, DeploymentStatus

    # Générer un slug unique pour ce tenant de pool
    pool_slug = f"pool-{_uuid.uuid4().hex[:8]}"
    db_name = pool_slug.replace('-', '_')  # ex: pool_a3f8c2ab
    project = DEFAULT_PROJECT
    region = DEFAULT_REGION
    cloud_sql_instance = DEFAULT_SQL_INST

    _log(pool_slug, 'POOL:PROVISION', f"Démarrage provisioning du tenant de pool '{pool_slug}'")

    # Créer le record Tenant de pool
    try:
        tenant = Tenant.objects.create(
            name=f"[POOL] {pool_slug}",
            slug=pool_slug,
            contact_email='pool@paramynd.com',
            db_name=db_name,
            gcp_project_id=project,
            cloud_run_region=region,
            cloud_sql_instance=cloud_sql_instance,
            status=TenantStatus.PROVISIONING,
            is_pool_tenant=True,
            pool_created_at=tz.now(),
        )
    except Exception as e:
        logger.error(f"[POOL:PROVISION] Impossible de créer le record Tenant pour '{pool_slug}': {e}")
        return

    image_uri = _get_latest_image_uri(project, region)
    image_tag = image_uri.split(':')[-1]

    deployment = Deployment.objects.create(
        tenant=tenant,
        image_tag=image_tag,
        image_uri=image_uri,
        status=DeploymentStatus.IN_PROGRESS,
        deployed_by='pool-provisioning',
    )

    # ── Étape 1 : Créer la BDD ────────────────────────────────────────────────
    tenant.provisioning_step = 'db_create'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    if not step_create_database(pool_slug, db_name, project):
        _log(pool_slug, 'POOL:DB_CREATE', 'Échec — abandon provisioning pool', error=True)
        _mark_failed(tenant, deployment, 'Échec création BDD pool')
        return

    # ── Étape 2 : Déployer Cloud Run (env vars neutres pour le pool) ──────────
    tenant.provisioning_step = 'cr_deploy'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    # Env vars neutres : le domaine sera écrasé lors de l'assignation
    pool_env_vars = {
        'PUBLIC_DOMAIN': f"{pool_slug}.paramynd.com",
        'PARAMYND_ADMIN_URL': getattr(__import__('django.conf', fromlist=['settings']).settings,
                                      'PARAMYND_ADMIN_URL', 'https://paramynd.com'),
    }

    ok, service_url = step_deploy_cloud_run(
        pool_slug, db_name, project, region, cloud_sql_instance, image_uri,
        env_vars=pool_env_vars,
    )
    if not ok:
        _log(pool_slug, 'POOL:CR_DEPLOY', 'Échec — abandon provisioning pool', error=True)
        _mark_failed(tenant, deployment, 'Échec déploiement Cloud Run pool')
        return

    tenant.cloud_run_url = service_url
    tenant.cloud_run_service_name = pool_slug
    tenant.current_image_tag = image_tag
    tenant.save(update_fields=['cloud_run_url', 'cloud_run_service_name', 'current_image_tag', 'updated_at'])

    # ── Étape 3 : Migrations ──────────────────────────────────────────────────
    tenant.provisioning_step = 'migrate'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    if not step_run_migrations(pool_slug, db_name, project, region, cloud_sql_instance, image_uri):
        _log(pool_slug, 'POOL:MIGRATE', 'Échec — abandon provisioning pool', error=True)
        _mark_failed(tenant, deployment, 'Échec migrations pool')
        return

    # ── Étape 4 : Marquer comme POOLED ───────────────────────────────────────
    from django.utils import timezone as tz2
    tenant.provisioning_step = 'done'
    tenant.status = TenantStatus.POOLED
    tenant.last_deployed_at = tz2.now()
    tenant.save(update_fields=['provisioning_step', 'status', 'last_deployed_at', 'updated_at'])

    deployment.status = DeploymentStatus.SUCCESS
    deployment.completed_at = tz2.now()
    deployment.save(update_fields=['status', 'completed_at'])

    _log(pool_slug, 'POOL:DONE', f"✅ Tenant de pool '{pool_slug}' prêt — en réserve.")


def ensure_pool_size(target_size: int = 3):
    """
    Vérifie la taille du pool et lance des provisions de pool si nécessaire.

    Compte les tenants POOLED + les tenants de pool en cours de provisioning.
    Si le total est inférieur à target_size, crée les tenants manquants en background.

    Args:
        target_size : Nombre de tenants de pool à maintenir (défaut: 3)
    """
    import threading
    from tenants.models import Tenant, TenantStatus

    # Compter les tenants POOLED disponibles + ceux en cours de provisioning
    pooled_count = Tenant.objects.filter(
        status=TenantStatus.POOLED,
        is_pool_tenant=True,
    ).count()
    provisioning_count = Tenant.objects.filter(
        status=TenantStatus.PROVISIONING,
        is_pool_tenant=True,
    ).count()

    total_in_pool = pooled_count + provisioning_count
    missing = target_size - total_in_pool

    if missing <= 0:
        logger.info(f"[POOL] Pool en bonne santé : {pooled_count} prêts, {provisioning_count} en cours (target={target_size})")
        return

    logger.info(f"[POOL] Pool insuffisant : {pooled_count} prêts + {provisioning_count} en cours = {total_in_pool} (target={target_size}). "
                f"Lancement de {missing} provisioning(s) de pool...")

    for i in range(missing):
        t = threading.Thread(
            target=provision_pool_tenant,
            daemon=False,
            name=f'pool-provision-{i}',
        )
        t.start()


# ──────────────────────────────────────────────────────────────────────────────
# FONCTION PRINCIPALE
# ──────────────────────────────────────────────────────────────────────────────


def provision_tenant(tenant_id: str, admin_email: str, admin_password: str):
    """
    Orchestrateur principal du provisioning d'un tenant.
    Doit être appelé en thread background.

    Args:
        tenant_id    : UUID du tenant à provisionner
        admin_email  : Email du client (sera son login)
        admin_password: Mot de passe choisi lors de l'inscription

    Gère les erreurs et met à jour tenant.status en conséquence.
    """
    from tenants.models import Tenant, TenantStatus, Deployment, DeploymentStatus

    # Recharger le tenant depuis la DB (on est dans un thread séparé)
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        logger.error(f"[PROVISION] Tenant {tenant_id} not found in DB")
        return

    slug              = tenant.slug
    db_name           = tenant.db_name or slug.replace('-', '_')
    project           = tenant.gcp_project_id or DEFAULT_PROJECT
    region            = tenant.cloud_run_region or DEFAULT_REGION
    cloud_sql_instance = tenant.cloud_sql_instance or DEFAULT_SQL_INST

    _log(slug, 'START', f"Starting full provisioning for tenant '{slug}' (db={db_name})")

    # Récupérer la dernière image
    image_uri = _get_latest_image_uri(project, region)
    image_tag = image_uri.split(':')[-1]
    _log(slug, 'START', f"Using image: {image_uri}")

    # Créer un enregistrement de déploiement
    deployment = Deployment.objects.create(
        tenant=tenant,
        image_tag=image_tag,
        image_uri=image_uri,
        status=DeploymentStatus.IN_PROGRESS,
        deployed_by='auto-provisioning',
    )

    errors = []

    # ── Étape 0 : Préparer ───────────────────────────────────────────────
    tenant.provisioning_step = 'db_create'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    # ── Étape 1 : Créer la DB ─────────────────────────────────────────────
    if not step_create_database(slug, db_name, project):
        errors.append('DATABASE_CREATE_FAILED')
        _log(slug, 'DB_CREATE', 'Failed — aborting provisioning', error=True)
        _mark_failed(tenant, deployment, 'Échec de création de la base de données')
        return

    # ── Étape 1.5 : Générer identifiants OAuth2 ───────────────────────────
    tenant.provisioning_step = 'oauth_setup'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    client_id, client_secret = step_create_oauth_app(tenant, admin_email)
    env_vars = {
        'SOCIAL_AUTH_PARAMYND_ADMIN_KEY': client_id,
        'SOCIAL_AUTH_PARAMYND_ADMIN_SECRET': client_secret,
        'PARAMYND_ADMIN_URL': getattr(settings, 'PARAMYND_ADMIN_URL', 'https://paramynd.com'),
        # PUBLIC_DOMAIN : domaine public du tenant, utilisé par CloudRunHostMiddleware
        # pour réécrire le header HTTP_HOST quand la requête arrive depuis .a.run.app
        'PUBLIC_DOMAIN': f"{tenant.slug}.paramynd.com",
    }

    # ── Étape 2 : Déployer Cloud Run ──────────────────────────────────────
    tenant.provisioning_step = 'cr_deploy'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    ok, service_url = step_deploy_cloud_run(
        slug, db_name, project, region, cloud_sql_instance, image_uri, env_vars=env_vars
    )
    if not ok:
        errors.append('CLOUD_RUN_DEPLOY_FAILED')
        _log(slug, 'CR_DEPLOY', 'Failed — aborting provisioning', error=True)
        _mark_failed(tenant, deployment, 'Échec du déploiement Cloud Run')
        return

    # Sauvegarder l'URL du service immédiatement
    tenant.cloud_run_url = service_url
    tenant.cloud_run_service_name = slug
    tenant.current_image_tag = image_tag
    tenant.save(update_fields=['cloud_run_url', 'cloud_run_service_name', 'current_image_tag', 'updated_at'])

    # Mettre à jour les URLs de l'app OAuth
    step_update_oauth_app_urls(tenant)

    # ── Étape 3 : Migrations ──────────────────────────────────────────────
    tenant.provisioning_step = 'migrate'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    if not step_run_migrations(slug, db_name, project, region, cloud_sql_instance, image_uri):
        errors.append('MIGRATE_FAILED')
        _log(slug, 'MIGRATE', 'Failed — marking tenant as failed', error=True)
        _mark_failed(tenant, deployment, 'Échec des migrations Django')
        return

    # ── Étape 4 : Créer le superuser ──────────────────────────────────────
    # Non bloquant : si ça échoue, le tenant reste accessible mais sans compte
    tenant.provisioning_step = 'superuser'
    tenant.save(update_fields=['provisioning_step', 'updated_at'])

    step_create_superuser(
        slug, db_name, project, region, cloud_sql_instance, image_uri,
        admin_email, admin_password
    )

    # ── Étape 5 : Marquer le tenant comme ACTIVE ──────────────────────────
    from tenants.models import TenantStatus
    tenant.provisioning_step = 'done'
    tenant.status = TenantStatus.ACTIVE
    tenant.last_deployed_at = timezone.now()
    tenant.save(update_fields=['provisioning_step', 'status', 'last_deployed_at', 'updated_at'])

    deployment.status = DeploymentStatus.SUCCESS
    deployment.completed_at = timezone.now()
    deployment.save(update_fields=['status', 'completed_at'])

    _log(slug, 'DONE', f"✅ Tenant '{slug}' provisioned successfully! URL: {service_url}")


def _mark_failed(tenant, deployment, error_message: str):
    """Marque le tenant et le déploiement comme échoués."""
    from tenants.models import TenantStatus, DeploymentStatus
    tenant.status = TenantStatus.FAILED
    tenant.save(update_fields=['status', 'updated_at'])
    deployment.status = DeploymentStatus.FAILED
    deployment.error_message = error_message
    deployment.completed_at = timezone.now()
    deployment.save(update_fields=['status', 'error_message', 'completed_at'])


def deprovision_tenant(tenant_id: str):
    """
    Supprime toutes les ressources GCP associées à un tenant, puis supprime le tenant de la base.
    Peut être exécuté de façon asynchrone ou synchrone.
    """
    from tenants.models import Tenant
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        logger.error(f"[DEPROVISION] Tenant {tenant_id} not found in DB")
        return

    slug = tenant.slug
    db_name = tenant.db_name or slug.replace('-', '_')
    project = tenant.gcp_project_id or DEFAULT_PROJECT
    region = tenant.cloud_run_region or DEFAULT_REGION

    _log(slug, 'DEPROVISION_START', f"Starting full deprovisioning for tenant '{slug}'")

    # 1. Supprimer le service Cloud Run
    _log(slug, 'CR_DELETE', f"Deleting Cloud Run service {slug}...")
    _run_gcloud([
        'run', 'services', 'delete', slug,
        f'--region={region}', f'--project={project}'
    ], slug, 'CR_DELETE', timeout=60)

    # 2. Supprimer les jobs Cloud Run
    _log(slug, 'CR_JOBS_DELETE', "Deleting Cloud Run jobs...")
    for job_suffix in ['migrate', 'superuser']:
        _run_gcloud([
            'run', 'jobs', 'delete', f"{slug}-{job_suffix}",
            f'--region={region}', f'--project={project}'
        ], slug, 'CR_JOBS_DELETE', timeout=30)

    # 3. Supprimer la base de données Cloud SQL
    _log(slug, 'DB_DELETE', f"Deleting Cloud SQL database {db_name}...")
    _run_gcloud([
        'sql', 'databases', 'delete', db_name,
        '--instance=yellow-db-paris',
        f'--project={project}'
    ], slug, 'DB_DELETE', timeout=120)

    # 4. Supprimer l'instance Tenant dans la base de données Django
    # Note: Cela déclenchera la suppression en cascade si d'autres objets sont liés (Deployment, etc.)
    _log(slug, 'DB_RECORD_DELETE', f"Deleting Tenant record for '{slug}'...")
    try:
        tenant.delete()
        _log(slug, 'DONE', f"✅ Tenant '{slug}' deprovisioned and deleted successfully.")
    except Exception as e:
        _log(slug, 'ERROR', f"Failed to delete Tenant record: {e}", error=True)
