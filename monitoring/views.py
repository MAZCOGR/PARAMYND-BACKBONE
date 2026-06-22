"""
monitoring/views.py — Vue de monitoring des logs Cloud Run
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from tenants.models import Tenant
from .services.logs import get_tenant_logs


@login_required
def logs_view(request):
    """Page de monitoring — sélecteur de tenant + logs Cloud Run."""
    tenants = Tenant.objects.filter(status__in=['active', 'provisioning']).order_by('name')
    selected_slug = request.GET.get('tenant', '')
    severity_filter = request.GET.get('severity', '')
    logs = []

    if selected_slug:
        logs = get_tenant_logs(
            tenant_slug=selected_slug,
            limit=100,
            severity=severity_filter or None,
        )

    context = {
        'page_title': 'Monitoring — Paramynd Admin',
        'tenants': tenants,
        'selected_slug': selected_slug,
        'severity_filter': severity_filter,
        'logs': logs,
        'severity_choices': [
            ('', 'Tous'),
            ('DEBUG', 'DEBUG'),
            ('INFO', 'INFO'),
            ('WARNING', 'WARNING'),
            ('ERROR', 'ERROR'),
            ('CRITICAL', 'CRITICAL'),
        ],
    }
    return render(request, 'monitoring/logs.html', context)


@login_required
def logs_api_view(request, tenant_slug):
    """API JSON — logs d'un tenant (pour rafraîchissement AJAX)."""
    severity = request.GET.get('severity', None)
    logs = get_tenant_logs(tenant_slug=tenant_slug, limit=50, severity=severity)
    return JsonResponse({'logs': logs})
