"""
tenants/api_urls.py — API REST pour les tenants (optionnel, pour les intégrations futures)
"""
from django.urls import path
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
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


urlpatterns = [
    path('', TenantListCreateView.as_view(), name='list_create'),
    path('<uuid:pk>/', TenantDetailView.as_view(), name='detail'),
    path('<uuid:pk>/deploy/', deploy_api_view, name='deploy'),
    path('tags/', tags_view, name='tags'),
]
