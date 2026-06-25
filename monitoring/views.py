"""
monitoring/views.py — Vue de monitoring des logs Cloud Run
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from tenants.models import Tenant
from .services.logs import get_service_logs


@login_required
def logs_view(request):
    """Page de monitoring — sélecteur de service (sans charger les logs)."""
    tenants = Tenant.objects.filter(status__in=['active', 'provisioning']).order_by('name')
    selected_service = request.GET.get('service', '')
    severity_filter = request.GET.get('severity', '')

    context = {
        'page_title': 'Monitoring — Paramynd Admin',
        'tenants': tenants,
        'selected_service': selected_service,
        'severity_filter': severity_filter,
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
def logs_table_partial_view(request):
    """Vue HTMX pour retourner les lignes du tableau de logs avec pagination."""
    service_name = request.GET.get('service', '')
    severity = request.GET.get('severity', '')
    page_token = request.GET.get('page_token', '')

    if not service_name:
        return render(request, 'monitoring/partials/logs_table_rows.html', {'logs': []})

    logs, next_page_token = get_service_logs(
        service_name=service_name, 
        limit=100, 
        severity=severity or None,
        page_token=page_token or None
    )

    context = {
        'logs': logs,
        'selected_service': service_name,
        'severity_filter': severity,
        'next_page_token': next_page_token,
    }
    return render(request, 'monitoring/partials/logs_table_rows.html', context)


@login_required
def logs_api_view(request, service_name):
    """API JSON — logs d'un service (pour ancienne compatibilité)."""
    severity = request.GET.get('severity', None)
    logs, _ = get_service_logs(service_name=service_name, limit=50, severity=severity)
    return JsonResponse({'logs': logs})
