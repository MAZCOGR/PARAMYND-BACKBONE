"""
tenants/services/artifact_registry.py
Lister les images/tags disponibles dans Google Artifact Registry.
"""
import logging
from typing import List, Dict
from django.conf import settings

logger = logging.getLogger(__name__)


def list_available_tags(limit: int = 10) -> List[Dict]:
    """
    Liste les tags Docker disponibles dans Artifact Registry.
    Retourne une liste de {'tag': str, 'digest': str, 'created': str, 'uri': str}
    """
    try:
        from google.cloud import artifactregistry_v1

        client = artifactregistry_v1.ArtifactRegistryClient()
        parent = (
            f"projects/{settings.GCP_PROJECT_ID}"
            f"/locations/{settings.GCP_REGION}"
            f"/repositories/{settings.ARTIFACT_REGISTRY_REPO}"
            f"/packages/{settings.PARAMYND_IMAGE_NAME}"
        )

        tags = list(client.list_tags(parent=parent))
        result = []
        for tag in tags[:limit]:
            uri = (
                f"{settings.GCP_REGION}-docker.pkg.dev"
                f"/{settings.GCP_PROJECT_ID}"
                f"/{settings.ARTIFACT_REGISTRY_REPO}"
                f"/{settings.PARAMYND_IMAGE_NAME}:{tag.name.split('/')[-1]}"
            )
            result.append({
                'tag': tag.name.split('/')[-1],
                'digest': tag.version.split('/')[-1] if tag.version else '',
                'created': '',
                'uri': uri,
            })
        return result

    except Exception as e:
        logger.warning(f"Artifact Registry non disponible : {e} — retour des données mock")
        # Mock data pour le développement local
        base_uri = (
            f"{settings.GCP_REGION}-docker.pkg.dev"
            f"/{settings.GCP_PROJECT_ID}"
            f"/{settings.ARTIFACT_REGISTRY_REPO}"
            f"/{settings.PARAMYND_IMAGE_NAME}"
        )
        return [
            {'tag': 'v1.3.0', 'digest': 'sha256:abc123', 'created': '2025-01-20', 'uri': f"{base_uri}:v1.3.0"},
            {'tag': 'v1.2.1', 'digest': 'sha256:def456', 'created': '2025-01-10', 'uri': f"{base_uri}:v1.2.1"},
            {'tag': 'v1.2.0', 'digest': 'sha256:ghi789', 'created': '2025-01-01', 'uri': f"{base_uri}:v1.2.0"},
            {'tag': 'v1.1.0', 'digest': 'sha256:jkl012', 'created': '2024-12-15', 'uri': f"{base_uri}:v1.1.0"},
            {'tag': 'latest',  'digest': 'sha256:abc123', 'created': '2025-01-20', 'uri': f"{base_uri}:latest"},
        ]


def get_image_uri(tag: str) -> str:
    """Construit l'URI complète d'une image pour un tag donné."""
    return (
        f"{settings.GCP_REGION}-docker.pkg.dev"
        f"/{settings.GCP_PROJECT_ID}"
        f"/{settings.ARTIFACT_REGISTRY_REPO}"
        f"/{settings.PARAMYND_IMAGE_NAME}:{tag}"
    )
