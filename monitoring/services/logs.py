"""
monitoring/services/logs.py
Wrapper autour de Google Cloud Logging pour récupérer les logs Cloud Run.
"""
import logging
from typing import List, Dict
from django.conf import settings

logger = logging.getLogger(__name__)


def get_tenant_logs(tenant_slug: str, limit: int = 100, severity: str = None) -> List[Dict]:
    """
    Récupère les logs Cloud Run d'un tenant via Cloud Logging.
    Retourne une liste de {'timestamp': str, 'severity': str, 'message': str}
    """
    service_name = f"paramynd-{tenant_slug}"

    try:
        from google.cloud import logging as gcloud_logging

        client = gcloud_logging.Client(project=settings.GCP_PROJECT_ID)

        filter_parts = [
            f'resource.type="cloud_run_revision"',
            f'resource.labels.service_name="{service_name}"',
        ]
        if severity:
            filter_parts.append(f'severity={severity}')

        log_filter = ' AND '.join(filter_parts)

        entries = client.list_entries(
            filter_=log_filter,
            page_size=limit,
            order_by=gcloud_logging.DESCENDING,
        )

        result = []
        for entry in entries:
            result.append({
                'timestamp': str(entry.timestamp) if entry.timestamp else '',
                'severity': entry.severity or 'DEFAULT',
                'message': entry.payload if isinstance(entry.payload, str) else str(entry.payload),
                'revision': entry.resource.labels.get('revision_name', '') if entry.resource else '',
            })
        return result

    except Exception as e:
        logger.warning(f"Cloud Logging non disponible : {e} — retour de logs mock")
        return [
            {
                'timestamp': '2025-01-20 10:05:01',
                'severity': 'INFO',
                'message': f'[{service_name}] Django démarré sur le port 8080',
                'revision': f'{service_name}-00003-xyz',
            },
            {
                'timestamp': '2025-01-20 10:05:02',
                'severity': 'INFO',
                'message': f'[{service_name}] GET /api/auth/me/ 200 12ms',
                'revision': f'{service_name}-00003-xyz',
            },
            {
                'timestamp': '2025-01-20 10:04:30',
                'severity': 'WARNING',
                'message': f'[{service_name}] DB connection pool: 4/5 connections used',
                'revision': f'{service_name}-00003-xyz',
            },
            {
                'timestamp': '2025-01-20 10:03:15',
                'severity': 'INFO',
                'message': f'[{service_name}] POST /api/auth/token/ 200 45ms',
                'revision': f'{service_name}-00003-xyz',
            },
            {
                'timestamp': '2025-01-20 10:00:00',
                'severity': 'INFO',
                'message': f'[{service_name}] Instance démarrée (mode mock — GCP non configuré)',
                'revision': f'{service_name}-00003-xyz',
            },
        ]
