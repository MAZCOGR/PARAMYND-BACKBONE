"""
tenants/views.py — Vues Django pour la gestion des tenants
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.db.models import Count
from functools import wraps

from .models import Tenant, Deployment, TenantStatus, DeploymentStatus, GitCommitRecord, CloudBuildRecord
from .forms import TenantCreateForm, TenantUpdateForm, DeployForm
from .services import artifact_registry, cloud_run, cloud_build, git_service


def admin_required(view_func):
    """Décorateur : accès réservé aux admins et superadmins."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, "Accès refusé — droits insuffisants.")
            return redirect('tenants:list')
        return view_func(request, *args, **kwargs)
    return wrapper


# ──────────────────────────────────────────────
# LISTE DES TENANTS
# ──────────────────────────────────────────────

@login_required
def tenant_list_view(request):
    """Liste les tenants. Les admins voient tout, les users voient leurs tenants uniquement."""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()

    # M-13 fix : les utilisateurs non-admin ne voient que leurs propres tenants
    if request.user.is_admin:
        tenants = Tenant.objects.all().order_by('-created_at')
    else:
        tenants = Tenant.objects.filter(
            contact_email=request.user.email
        ).order_by('-created_at')

    if status_filter:
        tenants = tenants.filter(status=status_filter)
    if search:
        tenants = tenants.filter(name__icontains=search) | \
                  tenants.filter(slug__icontains=search) | \
                  tenants.filter(contact_email__icontains=search)

    # Stats globales
    stats = {
        'total': Tenant.objects.count(),
        'active': Tenant.objects.filter(status=TenantStatus.ACTIVE).count(),
        'provisioning': Tenant.objects.filter(status=TenantStatus.PROVISIONING).count(),
        'failed': Tenant.objects.filter(status=TenantStatus.FAILED).count(),
    }

    # Formulaire de création pour le modal
    from .forms import TenantCreateForm
    from django.conf import settings
    form = TenantCreateForm(initial={
        'gcp_project_id': settings.GCP_PROJECT_ID,
        'cloud_run_region': settings.GCP_REGION,
        'cloud_sql_instance': getattr(settings, 'CLOUD_SQL_INSTANCE', ''),
    })

    context = {
        'page_title': 'Tenants — Paramynd Admin',
        'tenants': tenants,
        'stats': stats,
        'status_choices': TenantStatus.choices,
        'status_filter': status_filter,
        'search': search,
        'total_filtered': tenants.count(),
        'form': form,
    }
    return render(request, 'tenants/list.html', context)

@login_required
def tenant_choose_view(request):
    """Sélecteur d'espace pour les utilisateurs ayant plusieurs tenants."""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('tenants:list')
        
    tenants = Tenant.objects.filter(contact_email=request.user.email)
    
    if tenants.count() == 0:
        return redirect('/request-demo/')
    elif tenants.count() == 1:
        tenant = tenants.first()
        return redirect(f"{tenant.app_url}/auth/login/")
        
    context = {
        'page_title': 'Choisissez votre espace',
        'tenants': tenants,
    }
    return render(request, 'tenants/choose.html', context)


# ──────────────────────────────────────────────
# CRÉATION D'UN TENANT
# ──────────────────────────────────────────────

@admin_required
@require_http_methods(["GET", "POST"])
def tenant_create_view(request):
    """Créer un nouveau tenant."""
    if request.method == 'POST':
        form = TenantCreateForm(request.POST)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.cloud_run_service_name = tenant.service_name
            if not tenant.cloud_sql_instance:
                from django.conf import settings
                tenant.cloud_sql_instance = getattr(settings, 'CLOUD_SQL_INSTANCE', '')
            tenant.save()
            messages.success(request, f"Tenant « {tenant.name} » créé avec succès. Vous pouvez maintenant le déployer.")
            
            if request.headers.get('HX-Request'):
                from django.http import HttpResponse
                from django.urls import reverse
                response = HttpResponse(status=204)
                response['HX-Redirect'] = reverse('tenants:detail', kwargs={'pk': tenant.pk})
                return response
                
            return redirect('tenants:detail', pk=tenant.pk)
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'tenants/partials/create_form.html', {'form': form})
    else:
        from django.conf import settings
        form = TenantCreateForm(initial={
            'gcp_project_id': settings.GCP_PROJECT_ID,
            'cloud_run_region': settings.GCP_REGION,
            'cloud_sql_instance': getattr(settings, 'CLOUD_SQL_INSTANCE', ''),
        })

    context = {
        'page_title': 'Nouveau tenant — Paramynd Admin',
        'form': form,
    }
    return render(request, 'tenants/create.html', context)


# ──────────────────────────────────────────────
# DÉTAIL D'UN TENANT
# ──────────────────────────────────────────────

@login_required
def tenant_detail_view(request, pk):
    """Affiche le détail d'un tenant avec son historique de déploiements."""
    tenant = get_object_or_404(Tenant, pk=pk)
    deployments = tenant.deployments.order_by('-started_at')[:20]
    
    # 1. Charger les versions
    from .models import SaaSGitCommitRecord
    
    # Check artifact registry for tags to know what is built
    ar_tags = artifact_registry.list_available_tags(limit=100)
    ar_tag_names = {t['tag'] for t in ar_tags}

    saas_commits = SaaSGitCommitRecord.objects.all()[:30]
    available_tags = []
    seen_tags = set()
    for c in saas_commits:
        primary_tag = c.tag if c.tag else c.short_hash
        if primary_tag and primary_tag not in seen_tags:
            seen_tags.add(primary_tag)
            commit_msg = c.message.split('\n')[0][:50] + ('...' if len(c.message) > 50 else '')
            is_ready = primary_tag in ar_tag_names
            available_tags.append({
                'tag': primary_tag,
                'digest': c.short_hash,
                'created': c.date_str,
                'uri': artifact_registry.get_image_uri(primary_tag),
                'commit_msg': commit_msg,
                'author': c.author,
                'is_ready': is_ready
            })
            
    # 2. Fallback si l'historique en base est vide
    if not available_tags:
        available_tags = artifact_registry.list_available_tags()

    deploy_form = DeployForm(available_tags=available_tags)

    # Formulaire de mise à jour
    update_form = TenantUpdateForm(instance=tenant)
    if request.method == 'POST' and 'update_tenant' in request.POST:
        update_form = TenantUpdateForm(request.POST, instance=tenant)
        if update_form.is_valid():
            tenant = update_form.save()
            from tenants.services.provisioning import step_update_oauth_app_urls
            step_update_oauth_app_urls(tenant)
            messages.success(request, "Tenant mis à jour.")
            return redirect('tenants:detail', pk=pk)

    context = {
        'page_title': f'{tenant.name} — Paramynd Admin',
        'tenant': tenant,
        'deployments': deployments,
        'available_tags': available_tags,
        'deploy_form': deploy_form,
        'update_form': update_form,
        'status_choices': TenantStatus.choices,
    }
    return render(request, 'tenants/detail.html', context)


# ──────────────────────────────────────────────
# SUPPRESSION
# ──────────────────────────────────────────────

@admin_required
@require_POST
def tenant_delete_view(request, pk):
    """Supprime complètement un tenant et ses ressources associées."""
    tenant = get_object_or_404(Tenant, pk=pk)
    tenant_name = tenant.name
    tenant_id = tenant.id

    # Marquer immédiatement le tenant comme « en cours de suppression »
    # pour que la liste affiche le bon statut dès la redirection.
    tenant.status = TenantStatus.DELETING
    tenant.save(update_fields=['status'])

    # Lancement du déprovisionnement en arrière-plan
    import threading
    from tenants.services.provisioning import deprovision_tenant

    def _delete_and_remove(tid):
        deprovision_tenant(tid)
        # Une fois les ressources GCP supprimées, supprimer l'enregistrement en base
        try:
            Tenant.objects.filter(pk=tid).delete()
        except Exception:
            pass

    threading.Thread(target=_delete_and_remove, args=(tenant_id,), daemon=True).start()

    messages.success(request, f"La suppression du tenant « {tenant_name} » a été lancée. Il sera retiré de la liste une fois toutes les ressources supprimées.")
    return redirect('tenants:list')


# ──────────────────────────────────────────────
# RELANCER LE PROVISIONING (retry)
# ──────────────────────────────────────────────

@admin_required
@require_POST
def tenant_reprovision_view(request, pk):
    """
    Relance le provisioning complet d'un tenant bloqué en 'provisioning' ou 'failed'.
    Idempotent : toutes les étapes vérifient si les ressources existent déjà avant de les créer.
    Cas typique : thread daemon tué par un scale-down Cloud Run pendant le provisioning initial.
    """
    tenant = get_object_or_404(Tenant, pk=pk)

    if tenant.status not in (TenantStatus.PROVISIONING, TenantStatus.FAILED):
        messages.warning(
            request,
            f"Le tenant « {tenant.name} » est en statut {tenant.get_status_display()} — "
            "le reprovisioning n'est possible que pour les statuts 'En cours' ou 'En erreur'."
        )
        return redirect('tenants:detail', pk=pk)

    # Remettre en provisioning
    tenant.status = TenantStatus.PROVISIONING
    tenant.save(update_fields=['status'])

    # Générer un mot de passe temporaire aléatoire pour le superuser
    import secrets as _secrets
    temp_password = _secrets.token_urlsafe(16)

    # Relancer en thread background
    import threading
    from tenants.services.provisioning import provision_tenant

    t = threading.Thread(
        target=provision_tenant,
        args=(str(tenant.id), tenant.contact_email, temp_password),
        daemon=True,
        name=f'reprovision-{tenant.slug}',
    )
    t.start()

    messages.success(
        request,
        f"✅ Reprovisioning lancé pour « {tenant.name} ». "
        "Le statut passera à Actif dans quelques minutes."
    )
    return redirect('tenants:detail', pk=pk)



# ──────────────────────────────────────────────
# DÉPLOIEMENT
# ──────────────────────────────────────────────

@admin_required
@require_POST
def tenant_deploy_view(request, pk):
    """Lance un déploiement pour un tenant."""
    tenant = get_object_or_404(Tenant, pk=pk)
    
    # 1. Utiliser la même liste de tags que la vue de détail pour la validation
    from .models import SaaSGitCommitRecord
    saas_commits = SaaSGitCommitRecord.objects.all()[:30]
    
    ar_tags = artifact_registry.list_available_tags(limit=100)
    ar_tag_names = {t['tag'] for t in ar_tags}

    available_tags = []
    seen_tags = set()
    for c in saas_commits:
        primary_tag = c.tag if c.tag else c.short_hash
        if primary_tag and primary_tag not in seen_tags:
            seen_tags.add(primary_tag)
            is_ready = primary_tag in ar_tag_names
            available_tags.append({
                'tag': primary_tag,
                'uri': artifact_registry.get_image_uri(primary_tag),
                'is_ready': is_ready
            })
            
    if not available_tags:
        available_tags = artifact_registry.list_available_tags()
        
    form = DeployForm(request.POST, available_tags=available_tags)

    if not form.is_valid():
        messages.error(request, f"Formulaire invalide : {form.errors}")
        return redirect('tenants:detail', pk=pk)

    image_tag = form.cleaned_data['image_tag']
    image_uri = artifact_registry.get_image_uri(image_tag)

    # Créer l'entrée de déploiement en base
    deployment = Deployment.objects.create(
        tenant=tenant,
        image_tag=image_tag,
        image_uri=image_uri,
        status=DeploymentStatus.IN_PROGRESS,
        deployed_by=request.user.email,
    )

    # Mettre à jour le statut du tenant
    tenant.status = TenantStatus.PROVISIONING
    tenant.save(update_fields=['status'])

    # Récupérer les identifiants SSO existants si configurés
    env_vars = {}
    from oauth2_provider.models import Application
    from django.conf import settings
    import secrets
    app = Application.objects.filter(name=f"SSO-{tenant.slug}").first()
    if app:
        # Rotation du secret client pour éviter d'envoyer le hash de la DB
        new_secret = secrets.token_urlsafe(64)
        app.client_secret = new_secret
        app.save()
        
        env_vars = {
            'SOCIAL_AUTH_PARAMYND_ADMIN_KEY': app.client_id,
            'SOCIAL_AUTH_PARAMYND_ADMIN_SECRET': new_secret,
            'PARAMYND_ADMIN_URL': getattr(settings, 'PARAMYND_ADMIN_URL', 'https://paramynd.com'),
            # PUBLIC_DOMAIN : domaine public du tenant pour le CloudRunHostMiddleware
            'PUBLIC_DOMAIN': tenant.custom_domain if (tenant.custom_domain and tenant.domain_status == 'active') else f"{tenant.slug}.paramynd.com",
        }

    # Appel au service Cloud Run
    result = cloud_run.deploy_service(
        tenant_slug=tenant.slug,
        image_uri=image_uri,
        gcp_project_id=tenant.gcp_project_id,
        region=tenant.cloud_run_region,
        cloud_sql_instance=tenant.cloud_sql_instance,
        db_name=tenant.db_name,
        min_instances=form.cleaned_data.get('min_instances', 0),
        max_instances=form.cleaned_data.get('max_instances', 10),
        memory=form.cleaned_data.get('memory', '512Mi'),
        cpu=form.cleaned_data.get('cpu', '1'),
        env_vars=env_vars,
    )

    if result['success']:
        deployment.status = DeploymentStatus.SUCCESS
        deployment.revision_name = result.get('revision')
        deployment.completed_at = timezone.now()
        deployment.save()

        tenant.status = TenantStatus.ACTIVE
        tenant.current_image_tag = image_tag
        tenant.cloud_run_url = result.get('url')
        tenant.last_deployed_at = timezone.now()
        
        domain_notice = ""
        # Avec le Load Balancer GCP (URL Mask + Wildcard SSL), le sous-domaine est actif dès le déploiement !
        if tenant.custom_domain:
            from .models import DomainStatus
            tenant.domain_status = DomainStatus.ACTIVE
            tenant.dns_records = []
            domain_notice = " Domaine sécurisé (Load Balancer)."
                
        tenant.save()

        mock_notice = " (mode mock — GCP non configuré)" if result.get('mock') else ""
        messages.success(request, f"Déploiement réussi{mock_notice} : {image_tag} sur {tenant.name}.{domain_notice}")
    else:
        deployment.status = DeploymentStatus.FAILED
        deployment.error_message = result.get('error')
        deployment.completed_at = timezone.now()
        deployment.save()

        tenant.status = TenantStatus.FAILED
        tenant.save(update_fields=['status'])

        messages.error(request, f"Échec du déploiement : {result.get('error')}")

    return redirect('tenants:detail', pk=pk)


# ──────────────────────────────────────────────
# ROLLBACK
# ──────────────────────────────────────────────

@admin_required
@require_POST
def tenant_rollback_view(request, pk):
    """Rollback vers une révision Cloud Run spécifique."""
    tenant = get_object_or_404(Tenant, pk=pk)
    revision_name = request.POST.get('revision_name')

    if not revision_name:
        messages.error(request, "Nom de révision manquant.")
        return redirect('tenants:detail', pk=pk)

    result = cloud_run.rollback_to_revision(
        service_name=tenant.service_name,
        revision_name=revision_name,
        gcp_project_id=tenant.gcp_project_id,
        region=tenant.cloud_run_region,
    )

    if result['success']:
        mock_notice = " (mode mock)" if result.get('mock') else ""
        messages.success(request, f"Rollback effectué vers {revision_name}{mock_notice}.")
    else:
        messages.error(request, f"Échec du rollback : {result.get('error')}")

    return redirect('tenants:detail', pk=pk)


# ──────────────────────────────────────────────
# STATUT LIVE (AJAX)
# ──────────────────────────────────────────────

@login_required
def tenant_status_view(request, pk):
    """Retourne le statut live d'un service Cloud Run (JSON)."""
    tenant = get_object_or_404(Tenant, pk=pk)
    status_data = cloud_run.get_service_status(
        service_name=tenant.service_name,
        gcp_project_id=tenant.gcp_project_id,
        region=tenant.cloud_run_region,
    )
    return JsonResponse(status_data)


# ──────────────────────────────────────────────
# BUILDS
# ──────────────────────────────────────────────

@login_required
def builds_view(request):
    """Page principale des builds. Charge instantanément depuis la DB."""
    recent_commits = GitCommitRecord.objects.all()[:10]
    import datetime
    def parse_dt(s):
        try:
            return datetime.datetime.strptime(s, "%d/%m/%Y %H:%M")
        except:
            return datetime.datetime.min

    builds_list = list(CloudBuildRecord.objects.all()[:30])
    builds_list.sort(key=lambda x: parse_dt(x.created_str), reverse=True)
    
    from django.core.cache import cache
    hidden_builds = cache.get('hidden_builds', set())
    builds = [b for b in builds_list if b.build_id not in hidden_builds][:10]

    # Attach git commit info and format dates
    all_commits = {c.hash: c for c in GitCommitRecord.objects.all()}
    for b in builds:
        b.git_commit = all_commits.get(b.commit_sha)
        if not b.git_commit and b.commit_sha:
            for chash, c in all_commits.items():
                if chash.startswith(b.commit_sha):
                    b.git_commit = c
                    break
        
        # Parse '23/06/2026 04:11' to '23/06' and '04:11'
        parts = b.created_str.split(' ')
        if len(parts) == 2:
            date_part, time_part = parts
            b.short_date = date_part[:5]  # '23/06'
            b.short_time = time_part
        else:
            b.short_date = b.created_str
            b.short_time = ""

    total_tags = recent_commits.count()
    
    # Calculate KPIs in memory to avoid extra queries on small sets
    success_count = sum(1 for b in builds if b.status == 'SUCCESS')
    total_builds = len(builds)
    success_rate = round((success_count / total_builds) * 100) if total_builds > 0 else 0
    latest_status = builds[0].status if total_builds > 0 else 'N/A'

    context = {
        'recent_commits': recent_commits,
        'builds': builds,
        'total_tags': total_tags,
        'success_rate': success_rate,
        'latest_status': latest_status,
    }
    return render(request, 'tenants/builds.html', context)

@login_required
def builds_sync_view(request):
    """Point d'entrée asynchrone HTMX. Vérifie s'il y a de nouveaux commits ou builds."""
    from tenants.services.sync_service import sync_builds_and_commits
    has_changes = sync_builds_and_commits()
    
    if not has_changes:
        return HttpResponse(status=204)

    # Si changements, on récupère les nouvelles données pour redessiner la page
    recent_commits = GitCommitRecord.objects.all()[:10]
    import datetime
    def parse_dt(s):
        try:
            return datetime.datetime.strptime(s, "%d/%m/%Y %H:%M")
        except:
            return datetime.datetime.min

    builds_list = list(CloudBuildRecord.objects.all()[:30])
    builds_list.sort(key=lambda x: parse_dt(x.created_str), reverse=True)
    
    from django.core.cache import cache
    hidden_builds = cache.get('hidden_builds', set())
    builds = [b for b in builds_list if b.build_id not in hidden_builds][:10]
    
    # Attach git commit info and format dates
    all_commits = {c.hash: c for c in GitCommitRecord.objects.all()}
    for b in builds:
        b.git_commit = all_commits.get(b.commit_sha)
        if not b.git_commit and b.commit_sha:
            for chash, c in all_commits.items():
                if chash.startswith(b.commit_sha):
                    b.git_commit = c
                    break
                    
        # Parse '23/06/2026 04:11' to '23/06' and '04:11'
        parts = b.created_str.split(' ')
        if len(parts) == 2:
            date_part, time_part = parts
            b.short_date = date_part[:5]  # '23/06'
            b.short_time = time_part
        else:
            b.short_date = b.created_str
            b.short_time = ""
    
    total_tags = recent_commits.count()
    success_count = sum(1 for b in builds if b.status == 'SUCCESS')
    total_builds = len(builds)
    success_rate = round((success_count / total_builds) * 100) if total_builds > 0 else 0
    latest_status = builds[0].status if total_builds > 0 else 'N/A'

    context = {
        'recent_commits': recent_commits,
        'builds': builds,
        'total_tags': total_tags,
        'success_rate': success_rate,
        'latest_status': latest_status,
    }
    return render(request, 'tenants/partials/builds_sync_update.html', context)

@admin_required
@require_POST
def builds_delete_view(request, build_id):
    """Supprime un enregistrement de build et son image GCP.
    H-07 fix : admin_required au lieu de login_required.
    """
    import subprocess
    import logging
    logger = logging.getLogger(__name__)

    try:
        from django.core.cache import cache
        hidden_builds = cache.get('hidden_builds', set())
        hidden_builds.add(build_id)
        cache.set('hidden_builds', hidden_builds, None)
        
        build = CloudBuildRecord.objects.filter(build_id=build_id).first()
        if build:
            # Delete images from GCP if present
            if build.images:
                for image_uri in build.images:
                    try:
                        # Command: gcloud artifacts docker images delete IMAGE_URI --delete-tags --quiet
                        logger.info(f"Deleting image from GCP: {image_uri}")
                        result = subprocess.run(
                            ['gcloud', 'artifacts', 'docker', 'images', 'delete', image_uri, '--delete-tags', '--quiet'],
                            capture_output=True, text=True
                        )
                        if result.returncode != 0:
                            logger.error(f"Error deleting image {image_uri}: {result.stderr}")
                    except Exception as sub_e:
                        logger.error(f"Exception calling gcloud: {sub_e}")
                        
            build.delete()
            
        return JsonResponse({'success': True, 'message': 'Build et images supprimés avec succès.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def builds_rollback_view(request, build_id):
    """Effectue un rollback vers le commit associé à ce build (mock Cloud Run)."""
    # Ici, nous mettrions le code pour déplacer le trafic Cloud Run
    # vers la révision correspondant à l'image construite.
    return JsonResponse({'success': True, 'message': f'Rollback vers la révision de {build_id} simulé avec succès.'})

# ──────────────────────────────────────────────
# SAAS COMMITS
# ──────────────────────────────────────────────

def _build_saas_commits_context():
    """
    Helper privé : construit le contexte partagé entre la vue principale
    et la vue de synchronisation HTMX. Évite la duplication de logique.
    """
    from tenants.models import SaaSGitCommitRecord, Tenant, TenantStatus, Deployment, DeploymentStatus
    from django.utils import timezone
    from .services import artifact_registry
    import datetime

    # Vrai total en base (pas limité par le slice)
    total_commits = SaaSGitCommitRecord.objects.count()

    # Les 50 plus récents pour l'affichage (triés par commit_date_iso DESC via le Meta.ordering)
    recent_commits = list(SaaSGitCommitRecord.objects.all()[:50])

    now = timezone.now()
    commits_this_month = SaaSGitCommitRecord.objects.filter(
        commit_date_iso__year=now.year,
        commit_date_iso__month=now.month
    ).count()

    active_tenants = Tenant.objects.filter(status=TenantStatus.ACTIVE).count()
    tenants_this_month = Tenant.objects.filter(
        status=TenantStatus.ACTIVE,
        created_at__year=now.year,
        created_at__month=now.month
    ).count()

    thirty_days_ago = now - datetime.timedelta(days=30)
    recent_deployments = Deployment.objects.filter(started_at__gte=thirty_days_ago)
    total_recent = recent_deployments.count()
    if total_recent > 0:
        success_count = sum(1 for d in recent_deployments if d.status == DeploymentStatus.SUCCESS)
        success_rate = int((success_count / total_recent) * 100)
    else:
        success_rate = 100

    # Enrichissement : is_ready, short_date, short_time
    ar_tags = artifact_registry.list_available_tags(limit=100)
    ar_tag_names = {t['tag'] for t in ar_tags}

    for c in recent_commits:
        primary_tag = c.tag if c.tag else c.short_hash
        c.is_ready = primary_tag in ar_tag_names

        parts = c.date_str.split(' ')
        if len(parts) == 2:
            c.short_date = parts[0][:5]  # '23/06'
            c.short_time = parts[1]
        else:
            c.short_date = c.date_str
            c.short_time = ""

    return {
        'recent_commits':          recent_commits,
        'total_commits':           total_commits,
        'commits_this_month':      commits_this_month,
        'active_tenants':          active_tenants,
        'tenants_this_month':      tenants_this_month,
        'success_rate':            success_rate,
        'total_recent_deployments': total_recent,
    }


@login_required
def saas_commits_view(request):
    """
    Page principale des commits SaaS.
    Lance une sync en arrière-plan (thread non-bloquant) puis affiche
    immédiatement les données en DB. Le HTMX polling (every 30s) mettra
    à jour l'affichage quand la sync aura terminé.
    """
    import threading
    from tenants.services.sync_service import sync_builds_and_commits

    # Sync en background — ne bloque pas le rendu de la page
    t = threading.Thread(target=sync_builds_and_commits, daemon=True, name='saas-sync-view')
    t.start()

    context = _build_saas_commits_context()
    context['page_title'] = 'SaaS Commits — Paramynd Admin'
    return render(request, 'tenants/saas_commits.html', context)


@login_required
def saas_commits_sync_view(request):
    """
    Point d'entrée asynchrone HTMX pour SaaS.
    Retourne 204 (aucun changement) ou le HTML mis à jour.
    Le 204 est ignoré silencieusement par HTMX, ce qui permet
    au trigger 'every 30s' de continuer à fonctionner.
    """
    from tenants.services.sync_service import sync_builds_and_commits
    has_changes = sync_builds_and_commits()

    if not has_changes:
        # 204 = HTMX ne modifie rien et le trigger persiste
        return HttpResponse(status=204)

    context = _build_saas_commits_context()
    return render(request, 'tenants/partials/saas_commits_sync_update.html', context)
