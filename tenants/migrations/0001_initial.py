import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='Nom du client')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Slug (identifiant URL)')),
                ('contact_email', models.EmailField(blank=True, null=True, verbose_name='Email de contact')),
                ('status', models.CharField(choices=[('provisioning', 'En cours de provisionnement'), ('active', 'Actif'), ('paused', 'Mis en pause'), ('failed', 'En erreur'), ('archived', 'Archivé')], default='provisioning', max_length=20, verbose_name='Statut')),
                ('gcp_project_id', models.CharField(default='yellow-455523', max_length=255, verbose_name='Projet GCP')),
                ('cloud_run_region', models.CharField(default='europe-west9', max_length=50, verbose_name='Région Cloud Run')),
                ('cloud_run_service_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nom du service Cloud Run')),
                ('cloud_run_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='URL Cloud Run')),
                ('custom_domain', models.CharField(blank=True, max_length=255, null=True, verbose_name='Domaine personnalisé')),
                ('cloud_sql_instance', models.CharField(blank=True, help_text='ex: project:region:instance', max_length=500, null=True, verbose_name='Instance Cloud SQL')),
                ('db_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nom de la base de données')),
                ('current_image_tag', models.CharField(blank=True, max_length=255, null=True, verbose_name='Tag image courant')),
                ('last_deployed_at', models.DateTimeField(blank=True, null=True, verbose_name='Dernier déploiement')),
                ('notes', models.TextField(blank=True, verbose_name='Notes internes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
            ],
            options={
                'verbose_name': 'Tenant',
                'verbose_name_plural': 'Tenants',
                'db_table': 'tenants_tenant',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deployments', to='tenants.tenant', verbose_name='Tenant')),
                ('image_tag', models.CharField(max_length=255, verbose_name='Tag image')),
                ('image_uri', models.CharField(max_length=500, verbose_name='URI image complète')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('in_progress', 'En cours'), ('success', 'Réussi'), ('failed', 'Échoué'), ('rolled_back', 'Rollback effectué')], default='pending', max_length=20, verbose_name='Statut')),
                ('revision_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Révision Cloud Run')),
                ('deployed_by', models.CharField(blank=True, max_length=255, null=True, verbose_name='Déployé par')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name="Message d'erreur")),
                ('started_at', models.DateTimeField(auto_now_add=True, verbose_name='Démarré le')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Terminé le')),
            ],
            options={
                'verbose_name': 'Déploiement',
                'verbose_name_plural': 'Déploiements',
                'db_table': 'tenants_deployment',
                'ordering': ['-started_at'],
            },
        ),
    ]
