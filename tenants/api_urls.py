"""
tenants/api_urls.py — API REST pour les tenants (optionnel, pour les intégrations futures)
"""
from django.urls import path
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Tenant, Deployment
from .serializers import TenantSerializer, DeploymentSerializer, DeployRequestSerializer
from .services import artifact_registry, cloud_run

app_name = 'api_tenants'


class TenantListCreateView(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]


class TenantDetailView(generics.RetrieveUpdateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def tags_view(request):
    """GET /api/v1/tenants/tags/ — Liste des tags disponibles."""
    tags = artifact_registry.list_available_tags()
    return Response(tags)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def deploy_api_view(request, pk):
    """POST /api/v1/tenants/{id}/deploy/ — Déployer un tenant via API."""
    tenant = get_object_or_404(Tenant, pk=pk)
    serializer = DeployRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    image_tag = serializer.validated_data['image_tag']
    image_uri = artifact_registry.get_image_uri(image_tag)
    result = cloud_run.deploy_service(
        tenant_slug=tenant.slug,
        image_uri=image_uri,
        gcp_project_id=tenant.gcp_project_id,
        **{k: v for k, v in serializer.validated_data.items() if k != 'image_tag'}
    )

    if result['success']:
        return Response({'status': 'success', 'url': result.get('url'), 'revision': result.get('revision')})
    return Response({'status': 'error', 'detail': result.get('error')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])
def tenant_status_by_slug(request, slug):
    """
    GET /api/v1/tenants/status/<slug>/ — Statut de provisioning d'un tenant.

    Endpoint PUBLIC (pas d'auth) utilisé par building_workspace.html pour
    le polling toutes les 3s. Retourne le statut, l'étape courante et l'URL publique.

    Réponse :
        {
          "status": "provisioning" | "active" | "failed",
          "step": "db_create" | "oauth_setup" | "cr_deploy" | "migrate" | "superuser" | "done",
          "step_index": 0..6,
          "message": "...",
          "url": "https://<slug>.paramynd.com" | null
        }
    """
    # Mapping étape → (index 0-6, label affiché)
    STEP_MAP = {
        'db_create':   (0, 'Création de la base de données...'),
        'oauth_setup': (1, 'Configuration des ressources cloud...'),
        'cr_deploy':   (2, 'Déploiement de l\'application...'),
        'cr_update':   (2, 'Configuration de votre espace...'),   # Pool : mise à jour env vars
        'migrate':     (3, 'Application des migrations...'),
        'superuser':   (4, 'Création du compte administrateur...'),
        'done':        (5, 'Finalisation de l\'espace de travail...'),
    }

    # Recherche par slug direct OU par custom_domain (fallback pool tenant).
    # POURQUOI : assign_pool_tenant() redirige le frontend avec final_slug='acme'.
    # Pendant l'assignation, tenant.slug est encore 'pool-abc123' (pas renomme jusqu'a la fin).
    # Mais custom_domain='acme.paramynd.com' est set des le debut — ce Q fallback permet
    # donc au frontend de suivre la progression pendant toute la duree de l'assignation.
    # Une fois assign complete : tenant.slug='acme' et le lookup direct prend le relais.
    from django.db.models import Q
    try:
        tenant = Tenant.objects.get(
            Q(slug=slug) | Q(custom_domain=f"{slug}.paramynd.com")
        )
    except Tenant.DoesNotExist:
        return Response(
            {'status': 'not_found', 'url': None, 'message': 'Tenant introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Tenant.MultipleObjectsReturned:
        # Cas improbable — prendre le plus recent
        tenant = Tenant.objects.filter(
            Q(slug=slug) | Q(custom_domain=f"{slug}.paramynd.com")
        ).order_by('-updated_at').first()

    # URL publique = https://{slug}.paramynd.com (le slug = nom du service Cloud Run)
    public_url = f'https://{slug}.paramynd.com'
    if tenant.custom_domain and tenant.domain_status == 'active':
        public_url = f'https://{tenant.custom_domain}'

    if tenant.status == 'active':
        return Response({
            'status': 'active',
            'step': 'done',
            'step_index': 6,
            'url': public_url,
            'message': 'Votre espace est prêt !',
        })
    elif tenant.status == 'failed':
        # H-01 fix : ne pas exposer le message d'erreur interne dans un endpoint public
        return Response({
            'status': 'failed',
            'step': tenant.provisioning_step or '',
            'step_index': STEP_MAP.get(tenant.provisioning_step, (0, ''))[0],
            'url': None,
            'message': 'Le provisionnement a échoué. Contactez le support Paramynd.',
        })
    else:
        # provisioning / pooled / paused / archived → en cours
        step_key = tenant.provisioning_step or 'db_create'
        step_index, step_message = STEP_MAP.get(step_key, (0, 'Initialisation...'))
        return Response({
            'status': 'provisioning',
            'step': step_key,
            'step_index': step_index,
            'url': None,
            'message': step_message,
        })




urlpatterns = [
    path('', TenantListCreateView.as_view(), name='list_create'),
    path('<uuid:pk>/', TenantDetailView.as_view(), name='detail'),
    path('<uuid:pk>/deploy/', deploy_api_view, name='deploy'),
    path('tags/', tags_view, name='tags'),
    # ── Public endpoint — polling provisioning status ──
    path('status/<slug:slug>/', tenant_status_by_slug, name='status_by_slug'),
]
