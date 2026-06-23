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
    """Liste tous les tenants avec recherche et filtre par statut."""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()

    tenants = Tenant.objects.all().order_by('-created_at')

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

    context = {
        'page_title': 'Tenants — Paramynd Admin',
        'tenants': tenants,
        'stats': stats,
        'status_choices': TenantStatus.choices,
        'status_filter': status_filter,
        'search': search,
        'total_filtered': tenants.count(),
    }
    return render(request, 'tenants/list.html', context)


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
            return redirect('tenants:detail', pk=tenant.pk)
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
    available_tags = artifact_registry.list_available_tags()
    deploy_form = DeployForm(available_tags=available_tags)

    # Formulaire de mise à jour
    update_form = TenantUpdateForm(instance=tenant)
    if request.method == 'POST' and 'update_tenant' in request.POST:
        update_form = TenantUpdateForm(request.POST, instance=tenant)
        if update_form.is_valid():
            update_form.save()
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
# DÉPLOIEMENT
# ──────────────────────────────────────────────

@admin_required
@require_POST
def tenant_deploy_view(request, pk):
    """Lance un déploiement pour un tenant."""
    tenant = get_object_or_404(Tenant, pk=pk)
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
        tenant.save()

        mock_notice = " (mode mock — GCP non configuré)" if result.get('mock') else ""
        messages.success(request, f"Déploiement réussi{mock_notice} : {image_tag} sur {tenant.name}.")
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
        html = '<div id="sync-indicator" style="display:none;"></div>'
        return HttpResponse(html)

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

@login_required
@require_POST
def builds_delete_view(request, build_id):
    """Supprime un enregistrement de build et son image correspondante dans Artifact Registry."""
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

@login_required
def saas_commits_view(request):
    """Page principale des commits SaaS."""
    from tenants.models import SaaSGitCommitRecord, Tenant, TenantStatus, Deployment, DeploymentStatus
    from django.utils import timezone
    import datetime

    recent_commits = SaaSGitCommitRecord.objects.all()[:50]
    total_commits = recent_commits.count()

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

    for c in recent_commits:
        parts = c.date_str.split(' ')
        if len(parts) == 2:
            date_part, time_part = parts
            c.short_date = date_part[:5]  # '23/06'
            c.short_time = time_part
        else:
            c.short_date = c.date_str
            c.short_time = ""

    context = {
        'recent_commits': recent_commits,
        'total_commits': total_commits,
        'commits_this_month': commits_this_month,
        'active_tenants': active_tenants,
        'tenants_this_month': tenants_this_month,
        'success_rate': success_rate,
        'total_recent_deployments': total_recent,
        'page_title': 'SaaS Commits — Paramynd Admin',
    }
    return render(request, 'tenants/saas_commits.html', context)

@login_required
def saas_commits_sync_view(request):
    """Point d'entrée asynchrone HTMX pour SaaS."""
    from tenants.services.sync_service import sync_builds_and_commits
    has_changes = sync_builds_and_commits()
    
    if not has_changes:
        html = '<div id="saas-sync-indicator" style="display:none;"></div>'
        return HttpResponse(html)

    from tenants.models import SaaSGitCommitRecord, Tenant, TenantStatus, Deployment, DeploymentStatus
    from django.utils import timezone
    import datetime

    recent_commits = SaaSGitCommitRecord.objects.all()[:50]
    total_commits = recent_commits.count()

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

    for c in recent_commits:
        parts = c.date_str.split(' ')
        if len(parts) == 2:
            date_part, time_part = parts
            c.short_date = date_part[:5]  # '23/06'
            c.short_time = time_part
        else:
            c.short_date = c.date_str
            c.short_time = ""

    context = {
        'recent_commits': recent_commits,
        'total_commits': total_commits,
        'commits_this_month': commits_this_month,
        'active_tenants': active_tenants,
        'tenants_this_month': tenants_this_month,
        'success_rate': success_rate,
        'total_recent_deployments': total_recent,
    }
    return render(request, 'tenants/partials/saas_commits_sync_update.html', context)


