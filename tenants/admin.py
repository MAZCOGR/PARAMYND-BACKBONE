from django.contrib import admin
from .models import Tenant, Deployment, TenantStatus


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'gcp_project_id', 'current_image_tag', 'last_deployed_at', 'created_at')
    list_filter = ('status', 'gcp_project_id', 'cloud_run_region')
    search_fields = ('name', 'slug', 'contact_email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Informations client', {'fields': ('id', 'name', 'slug', 'contact_email', 'status', 'notes')}),
        ('GCP Configuration', {'fields': ('gcp_project_id', 'cloud_run_region', 'cloud_run_service_name', 'cloud_run_url', 'custom_domain')}),
        ('Base de données', {'fields': ('cloud_sql_instance', 'db_name')}),
        ('Déploiement', {'fields': ('current_image_tag', 'last_deployed_at')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'image_tag', 'status', 'deployed_by', 'started_at', 'completed_at')
    list_filter = ('status', 'tenant')
    search_fields = ('tenant__name', 'tenant__slug', 'image_tag', 'deployed_by')
    readonly_fields = ('id', 'started_at')
    ordering = ('-started_at',)
