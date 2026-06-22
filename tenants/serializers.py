"""
tenants/serializers.py — Serializers DRF pour l'API tenants
"""
from rest_framework import serializers
from .models import Tenant, Deployment, TenantStatus, DeploymentStatus


class TenantSerializer(serializers.ModelSerializer):
    service_name = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'contact_email', 'status', 'status_display',
            'gcp_project_id', 'cloud_run_region', 'cloud_run_service_name',
            'cloud_run_url', 'custom_domain', 'cloud_sql_instance', 'db_name',
            'current_image_tag', 'last_deployed_at', 'service_name',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'service_name']


class DeploymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.ReadOnlyField()

    class Meta:
        model = Deployment
        fields = [
            'id', 'tenant', 'image_tag', 'image_uri', 'status', 'status_display',
            'revision_name', 'deployed_by', 'error_message',
            'started_at', 'completed_at', 'duration',
        ]
        read_only_fields = ['id', 'started_at']


class DeployRequestSerializer(serializers.Serializer):
    image_tag = serializers.CharField(max_length=255)
    min_instances = serializers.IntegerField(default=0, min_value=0)
    max_instances = serializers.IntegerField(default=10, min_value=1, max_value=100)
    memory = serializers.ChoiceField(choices=['256Mi', '512Mi', '1Gi', '2Gi'], default='512Mi')
    cpu = serializers.ChoiceField(choices=['1', '2', '4'], default='1')
