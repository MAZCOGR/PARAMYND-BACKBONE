"""
tenants/models.py — Modèles Tenant et Deployment pour le control plane
"""
import uuid
import re
import enum
from django.db import models
from django.utils import timezone


class TenantStatus(models.TextChoices):
    PROVISIONING = 'provisioning', 'En cours de provisionnement'
    ACTIVE       = 'active',       'Actif'
    PAUSED       = 'paused',       'Mis en pause'
    FAILED       = 'failed',       'En erreur'
    ARCHIVED     = 'archived',     'Archivé'


class DomainStatus(models.TextChoices):
    NONE     = 'none',     'Non configuré'
    PENDING  = 'pending',  'En attente de propagation DNS'
    ACTIVE   = 'active',   'Actif et sécurisé'
    FAILED   = 'failed',   'Échec de configuration'


class DeploymentStatus(models.TextChoices):
    PENDING     = 'pending',     'En attente'
    IN_PROGRESS = 'in_progress', 'En cours'
    SUCCESS     = 'success',     'Réussi'
    FAILED      = 'failed',      'Échoué'
    ROLLED_BACK = 'rolled_back', 'Rollback effectué'


class Tenant(models.Model):
    """
    Représente un client (tenant) Paramynd avec son instance Cloud Run.
    Chaque tenant a son propre service Cloud Run et sa propre DB PostgreSQL.
    """
    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name                  = models.CharField(max_length=255, verbose_name='Nom du client')
    slug                  = models.SlugField(max_length=100, unique=True, db_index=True, verbose_name='Slug (identifiant URL)')
    contact_email         = models.EmailField(blank=True, null=True, verbose_name='Email de contact')
    status                = models.CharField(max_length=20, choices=TenantStatus.choices, default=TenantStatus.PROVISIONING, verbose_name='Statut')

    # GCP Config
    gcp_project_id        = models.CharField(max_length=255, default='yellow-455523', verbose_name='Projet GCP')
    cloud_run_region      = models.CharField(max_length=50, default='europe-west9', verbose_name='Région Cloud Run')
    cloud_run_service_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nom du service Cloud Run')
    cloud_run_url         = models.URLField(max_length=500, blank=True, null=True, verbose_name='URL Cloud Run')
    
    # Custom Domain
    custom_domain         = models.CharField(max_length=255, blank=True, null=True, verbose_name='Domaine personnalisé')
    domain_status         = models.CharField(max_length=20, choices=DomainStatus.choices, default=DomainStatus.NONE, verbose_name='Statut du domaine')
    dns_records           = models.JSONField(blank=True, null=True, verbose_name='Enregistrements DNS requis')

    # Cloud SQL
    cloud_sql_instance    = models.CharField(max_length=500, blank=True, null=True, verbose_name='Instance Cloud SQL', help_text='ex: project:region:instance')
    db_name               = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nom de la base de données')

    # Déploiement courant
    current_image_tag     = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tag image courant')
    last_deployed_at      = models.DateTimeField(blank=True, null=True, verbose_name='Dernier déploiement')

    # Métadonnées
    notes                 = models.TextField(blank=True, verbose_name='Notes internes')
    created_at            = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at            = models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')

    class Meta:
        db_table = 'tenants_tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.slug})"

    @property
    def service_name(self):
        """Nom du service Cloud Run : {slug}"""
        return self.slug

    @property
    def app_url(self):
        """Retourne l'URL personnalisée si elle est active, sinon l'URL Cloud Run."""
        if self.custom_domain and self.domain_status == 'active':
            return f"https://{self.custom_domain}"
        return self.cloud_run_url

    @property
    def status_badge_class(self):
        """Classe CSS pour le badge de statut."""
        classes = {
            TenantStatus.ACTIVE:       'badge-active',
            TenantStatus.PROVISIONING: 'badge-provisioning',
            TenantStatus.PAUSED:       'badge-paused',
            TenantStatus.FAILED:       'badge-failed',
            TenantStatus.ARCHIVED:     'badge-archived',
        }
        return classes.get(self.status, 'badge-default')

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.slug and not re.match(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$', self.slug):
            raise ValidationError({'slug': 'Le slug doit être en minuscules, alphanumérique avec tirets, 3-30 caractères.'})


class Deployment(models.Model):
    """
    Historique des déploiements pour chaque tenant.
    Chaque déploiement correspond à un push d'image sur Cloud Run.
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant        = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='deployments', verbose_name='Tenant')
    image_tag     = models.CharField(max_length=255, verbose_name='Tag image')
    image_uri     = models.CharField(max_length=500, verbose_name='URI image complète')
    status        = models.CharField(max_length=20, choices=DeploymentStatus.choices, default=DeploymentStatus.PENDING, verbose_name='Statut')
    revision_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Révision Cloud Run')
    deployed_by   = models.CharField(max_length=255, blank=True, null=True, verbose_name='Déployé par')
    error_message = models.TextField(blank=True, null=True, verbose_name="Message d'erreur")
    started_at    = models.DateTimeField(auto_now_add=True, verbose_name='Démarré le')
    completed_at  = models.DateTimeField(blank=True, null=True, verbose_name='Terminé le')

    class Meta:
        db_table = 'tenants_deployment'
        verbose_name = 'Déploiement'
        verbose_name_plural = 'Déploiements'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.tenant.slug} — {self.image_tag} ({self.get_status_display()})"

    @property
    def duration(self):
        """Durée du déploiement en secondes."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class GitCommitRecord(models.Model):
    """Cache en base de données de l'historique Git."""
    hash = models.CharField(max_length=40, primary_key=True, verbose_name="Hash complet")
    short_hash = models.CharField(max_length=10, verbose_name="Hash court")
    message = models.TextField(verbose_name="Message du commit")
    author = models.CharField(max_length=255, verbose_name="Auteur")
    date_str = models.CharField(max_length=100, verbose_name="Date string")
    commit_date_iso = models.DateTimeField(blank=True, null=True, verbose_name="Date ISO du commit")
    branch = models.CharField(max_length=255, blank=True, null=True, verbose_name="Branche")
    tag = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tag")
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenants_git_commit'
        verbose_name = 'Commit Git'
        ordering = ['-fetched_at']


class CloudBuildRecord(models.Model):
    """Cache en base de données de l'historique Cloud Build."""
    build_id = models.CharField(max_length=100, primary_key=True, verbose_name="ID du build")
    status = models.CharField(max_length=50, verbose_name="Statut")
    progress = models.IntegerField(default=0, verbose_name="Progression (%)")
    created_str = models.CharField(max_length=100, verbose_name="Créé le")
    duration = models.CharField(max_length=50, verbose_name="Durée")
    commit_sha = models.CharField(max_length=40, blank=True, null=True, verbose_name="Commit SHA")
    branch_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom de branche")
    tags = models.JSONField(default=list, verbose_name="Tags")
    images = models.JSONField(default=list, verbose_name="Images Docker")
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenants_cloud_build'
        verbose_name = 'Cloud Build'
        ordering = ['-fetched_at']


class SaaSGitCommitRecord(models.Model):
    """Cache en base de données de l'historique Git du SaaS."""
    hash = models.CharField(max_length=40, primary_key=True, verbose_name="Hash complet")
    short_hash = models.CharField(max_length=10, verbose_name="Hash court")
    message = models.TextField(verbose_name="Message du commit")
    author = models.CharField(max_length=255, verbose_name="Auteur")
    date_str = models.CharField(max_length=100, verbose_name="Date string")
    commit_date_iso = models.DateTimeField(blank=True, null=True, verbose_name="Date ISO du commit")
    branch = models.CharField(max_length=255, blank=True, null=True, verbose_name="Branche")
    tag = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tag")
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenants_saas_git_commit'
        verbose_name = 'Commit Git SaaS'
        ordering = ['-fetched_at']

