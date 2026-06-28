"""
tenants/migrations/0010_add_pool_status_and_fields.py
Ajoute le statut POOLED et les champs is_pool_tenant / pool_created_at au modèle Tenant.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0009_add_provisioning_step'),
    ]

    operations = [
        # Ajouter les nouveaux champs
        migrations.AddField(
            model_name='tenant',
            name='is_pool_tenant',
            field=models.BooleanField(
                default=False,
                verbose_name='Tenant de pool',
                help_text='True si ce tenant est un tenant de réserve (pas encore assigné à un client).',
            ),
        ),
        migrations.AddField(
            model_name='tenant',
            name='pool_created_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Créé dans le pool le',
                help_text="Date à laquelle ce tenant a été placé dans le pool.",
            ),
        ),
        # Mettre à jour le champ status pour inclure le choix 'pooled'
        migrations.AlterField(
            model_name='tenant',
            name='status',
            field=models.CharField(
                choices=[
                    ('provisioning', 'En cours de provisionnement'),
                    ('pooled',       'En réserve (pool)'),
                    ('active',       'Actif'),
                    ('paused',       'Mis en pause'),
                    ('failed',       'En erreur'),
                    ('archived',     'Archivé'),
                    ('deleting',     'Suppression en cours'),
                ],
                default='provisioning',
                max_length=20,
                verbose_name='Statut',
            ),
        ),
    ]
