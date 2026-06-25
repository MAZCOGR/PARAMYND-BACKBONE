"""
monitoring/services/logs.py
Wrapper autour de Google Cloud Logging pour récupérer les logs Cloud Run.
"""
import logging
import hashlib
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Connection pooling : Instanciation globale et paresseuse du client GCP
_gcp_logging_client = None

def get_gcp_logging_client():
    global _gcp_logging_client
    if _gcp_logging_client is None:
        try:
            from google.cloud import logging as gcloud_logging
            _gcp_logging_client = gcloud_logging.Client(project=settings.GCP_PROJECT_ID)
            logger.info("GCP Logging Client initialisé avec succès.")
        except Exception as e:
            logger.warning(f"GCP Logging Client non disponible : {e}")
    return _gcp_logging_client


def get_service_logs(service_name: str, limit: int = 100, severity: str = None, page_token: str = None) -> Tuple[List[Dict], str]:
    """
    Récupère les logs Cloud Run d'un service via Cloud Logging avec pagination.
    Retourne (liste_de_logs, next_page_token)
    """
    # Cache courte durée (5s) pour limiter le spam de rafraîchissements
    cache_key_str = f"logs_{service_name}_{severity}_{page_token}_{limit}"
    cache_key = hashlib.md5(cache_key_str.encode('utf-8')).hexdigest()
    
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    client = get_gcp_logging_client()

    if client:
        try:
            from google.cloud import logging as gcloud_logging

            filter_parts = [
                f'resource.type="cloud_run_revision"',
                f'resource.labels.service_name="{service_name}"',
            ]
            if severity:
                filter_parts.append(f'severity={severity}')

            # Limite temporelle pour optimiser la recherche de logs massifs
            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            filter_parts.append(f'timestamp >= "{seven_days_ago}"')

            log_filter = ' AND '.join(filter_parts)

            iterator = client.list_entries(
                filter_=log_filter,
                page_size=limit,
                order_by=gcloud_logging.DESCENDING,
                page_token=page_token
            )

            # Extraire exactement une page
            pages = iterator.pages
            try:
                page = next(pages)
                entries = list(page)
                # Google gère la propriété next_page_token directement sur l'itérateur après extraction
                next_token = iterator.next_page_token
            except StopIteration:
                entries = []
                next_token = None

            result = []
            for entry in entries:
                result.append({
                    'timestamp': str(entry.timestamp) if entry.timestamp else '',
                    'severity': entry.severity or 'DEFAULT',
                    'message': entry.payload if isinstance(entry.payload, str) else str(entry.payload),
                    'revision': entry.resource.labels.get('revision_name', '') if entry.resource else '',
                })

            final_result = (result, next_token)
            cache.set(cache_key, final_result, timeout=5)
            return final_result

        except Exception as e:
            logger.error(f"Erreur API Cloud Logging : {e}")

    # Fallback / Mode Mock si GCP échoue ou en dev local
    logger.warning(f"Retour de logs MOCK pour {service_name}")
    
    if page_token:
        # Fin de pagination pour le mock
        return [], None

    mock_logs = [
        {
            'timestamp': '2025-01-20 10:05:01',
            'severity': 'INFO',
            'message': f'[{service_name}] Django démarré sur le port 8080 (MOCK)',
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
    return mock_logs, None
