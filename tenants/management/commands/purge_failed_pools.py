"""
Management command to purge all failed/orphaned pool tenants from the database.
Usage: python manage.py purge_failed_pools [--dry-run]
"""
from django.core.management.base import BaseCommand
from tenants.models import Tenant, TenantStatus


class Command(BaseCommand):
    help = 'Purge failed/orphaned pool tenants from the database'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        qs = Tenant.objects.filter(is_pool_tenant=True, status=TenantStatus.FAILED)
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No failed pool tenants found. All clean!'))
            return

        self.stdout.write(f'Found {count} failed pool tenant(s):')
        for t in qs:
            self.stdout.write(f'  - {t.slug} (created: {t.created_at}, step: {t.provisioning_step})')

        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would delete {count} tenant(s). Run without --dry-run to proceed.'))
        else:
            deleted, _ = qs.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} failed pool tenant(s) successfully.'))
