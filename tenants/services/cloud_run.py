"""
tenants/services/cloud_run.py
Wrapper autour de Google Cloud Run Admin API v2.
Graceful degradation : retourne des données mock si les SDKs GCP ne sont pas configurés.
"""
import logging
from typing import Optional, List, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Retourne un client Cloud Run ou None si non configuré."""
    try:
        from google.cloud import run_v2
        return run_v2.ServicesClient()
    except Exception as e:
        logger.warning(f"Cloud Run SDK non disponible : {e}")
        return None


def _get_v1_domain_client():
    """Retourne un client Cloud Run v1 pour les DomainMappings, ou None."""
    try:
        from google.cloud import run_v1
        return run_v1.DomainMappingsClient()
    except Exception as e:
        logger.warning(f"Cloud Run v1 SDK non disponible (DomainMappings) : {e}")
        return None


def deploy_service(
    tenant_slug: str,
    image_uri: str,
    gcp_project_id: str,
    region: str = None,
    env_vars: Optional[Dict[str, str]] = None,
    cloud_sql_instance: Optional[str] = None,
    db_name: Optional[str] = None,
    min_instances: int = 0,
    max_instances: int = 10,
    memory: str = "512Mi",
    cpu: str = "1",
) -> Dict[str, Any]:
    """
    Déploie ou met à jour un service Cloud Run pour un tenant.
    Retourne {'success': bool, 'url': str, 'revision': str, 'error': str}
    """
    if region is None:
        region = settings.GCP_REGION

    service_name = tenant_slug
    client = _get_client()

    if client is None:
        # Mode mock — utile en développement sans GCP configuré
        logger.info(f"[MOCK] Déploiement simulé : {service_name} avec {image_uri}")
        return {
            'success': True,
            'url': f"https://{service_name}-mock.a.run.app",
            'revision': f"{service_name}-00001-abc",
            'error': None,
            'mock': True,
        }

    try:
        from google.cloud import run_v2

        parent = f"projects/{gcp_project_id}/locations/{region}"
        service_fqn = f"{parent}/services/{service_name}"

        # Construire les variables d'environnement
        base_env = {
            'DJANGO_SETTINGS_MODULE': 'core.settings',
            'DB_NAME': db_name or tenant_slug.replace('-', '_'),
            'DB_USER': 'admin',
        }
        if cloud_sql_instance:
            base_env['CLOUD_SQL_INSTANCE'] = cloud_sql_instance
        if env_vars:
            base_env.update(env_vars)

        env_list = [
            run_v2.EnvVar(name=k, value=v)
            for k, v in base_env.items()
        ]

        # Injecter les secrets GCP (DB_PASSWORD + SECRET_KEY) depuis Secret Manager
        env_list += [
            run_v2.EnvVar(
                name='DB_PASSWORD',
                value_source=run_v2.EnvVarSource(
                    secret_key_ref=run_v2.SecretKeySelector(
                        secret='DB_PASS',
                        version='latest'
                    )
                )
            ),
            run_v2.EnvVar(
                name='SECRET_KEY',
                value_source=run_v2.EnvVarSource(
                    secret_key_ref=run_v2.SecretKeySelector(
                        secret='PARAMYND_SECRET_KEY',
                        version='latest'
                    )
                )
            ),
        ]

        # Volume Cloud SQL
        volumes = []
        volume_mounts = []
        if cloud_sql_instance:
            volumes.append(run_v2.Volume(
                name='cloudsql',
                cloud_sql_instance=run_v2.CloudSqlInstance(
                    instances=[cloud_sql_instance]
                )
            ))
            volume_mounts.append(run_v2.VolumeMount(
                name='cloudsql',
                mount_path='/cloudsql'
            ))

        container = run_v2.Container(
            image=image_uri,
            env=env_list,
            resources=run_v2.ResourceRequirements(
                limits={'memory': memory, 'cpu': cpu}
            ),
            volume_mounts=volume_mounts,
        )

        service = run_v2.Service(
            template=run_v2.RevisionTemplate(
                containers=[container],
                volumes=volumes,
                scaling=run_v2.RevisionScaling(
                    min_instance_count=min_instances,
                    max_instance_count=max_instances,
                ),
            ),
            ingress=run_v2.IngressTraffic.INGRESS_TRAFFIC_ALL,
        )

        # Vérifier si le service existe déjà
        try:
            client.get_service(name=service_fqn)
            exists = True
        except Exception as e:
            if "NotFound" in str(type(e).__name__) or "404" in str(e):
                exists = False
            else:
                # Une autre erreur (ex: permission refusée), on la relève
                raise e

        if exists:
            # Le service existe → on le met à jour
            service.name = service_fqn
            operation = client.update_service(service=service)
        else:
            # Le service n'existe pas → on le crée
            operation = client.create_service(
                parent=parent,
                service=service,
                service_id=service_name,
            )

        result = operation.result(timeout=300)
        revision = result.latest_created_revision if hasattr(result, 'latest_created_revision') else 'unknown'

        # Rendre le service public (non authentifié)
        try:
            policy = client.get_iam_policy(request={'resource': service_fqn})
            binding_found = False
            for b in policy.bindings:
                if b.role == 'roles/run.invoker':
                    if 'allUsers' not in b.members:
                        b.members.append('allUsers')
                    binding_found = True
                    break
            if not binding_found:
                policy.bindings.add(role='roles/run.invoker', members=['allUsers'])
            client.set_iam_policy(request={'resource': service_fqn, 'policy': policy})
            logger.info(f"Permissions IAM configurées pour rendre {service_name} public.")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration IAM publique pour {service_name}: {e}")

        return {
            'success': True,
            'url': result.uri if hasattr(result, 'uri') else '',
            'revision': revision,
            'error': None,
            'mock': False,
        }

    except Exception as e:
        logger.error(f"Erreur déploiement Cloud Run {service_name}: {e}")
        return {
            'success': False,
            'url': None,
            'revision': None,
            'error': str(e),
            'mock': False,
        }


def get_service_status(service_name: str, gcp_project_id: str, region: str = None) -> Dict[str, Any]:
    """Retourne le statut live d'un service Cloud Run."""
    if region is None:
        region = settings.GCP_REGION

    client = _get_client()
    if client is None:
        return {
            'status': 'unknown',
            'url': None,
            'latest_revision': None,
            'mock': True,
        }

    try:
        from google.cloud import run_v2
        name = f"projects/{gcp_project_id}/locations/{region}/services/{service_name}"
        service = client.get_service(name=name)
        return {
            'status': 'active',
            'url': service.uri,
            'latest_revision': service.latest_created_revision,
            'mock': False,
        }
    except Exception as e:
        logger.error(f"Erreur statut Cloud Run {service_name}: {e}")
        return {'status': 'error', 'url': None, 'latest_revision': None, 'error': str(e)}


def list_revisions(service_name: str, gcp_project_id: str, region: str = None) -> List[Dict]:
    """Liste les révisions d'un service Cloud Run."""
    if region is None:
        region = settings.GCP_REGION

    client = _get_client()
    if client is None:
        return [
            {'name': f'{service_name}-00001-aaa', 'created': '2025-01-01', 'active': True},
            {'name': f'{service_name}-00002-bbb', 'created': '2025-01-15', 'active': False},
        ]

    try:
        from google.cloud import run_v2
        revisions_client = run_v2.RevisionsClient()
        parent = f"projects/{gcp_project_id}/locations/{region}/services/{service_name}"
        revisions = list(revisions_client.list_revisions(parent=parent))
        return [
            {
                'name': r.name.split('/')[-1],
                'created': str(r.create_time),
                'active': True,
            }
            for r in revisions[:10]
        ]
    except Exception as e:
        logger.error(f"Erreur liste révisions {service_name}: {e}")
        return []


def rollback_to_revision(
    service_name: str,
    revision_name: str,
    gcp_project_id: str,
    region: str = None,
) -> Dict[str, Any]:
    """Effectue un rollback vers une révision spécifique."""
    if region is None:
        region = settings.GCP_REGION

    client = _get_client()
    if client is None:
        logger.info(f"[MOCK] Rollback simulé : {service_name} → {revision_name}")
        return {'success': True, 'mock': True}

    try:
        from google.cloud import run_v2
        service_fqn = f"projects/{gcp_project_id}/locations/{region}/services/{service_name}"
        service = client.get_service(name=service_fqn)

        # Forcer 100% du trafic sur la révision cible
        service.traffic = [
            run_v2.TrafficTarget(
                type_=run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION,
                revision=revision_name,
                percent=100,
            )
        ]
        operation = client.update_service(service=service)
        operation.result(timeout=120)
        return {'success': True, 'mock': False}
    except Exception as e:
        logger.error(f"Erreur rollback {service_name}: {e}")
        return {'success': False, 'error': str(e)}

