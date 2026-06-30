#!/usr/bin/env python
"""
Script de nettoyage des pool tenants en erreur.
Exécuté via Cloud Run Job.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.models import Tenant, TenantStatus

failed_qs = Tenant.objects.filter(is_pool_tenant=True, status=TenantStatus.FAILED)
count = failed_qs.count()
print(f"Found {count} failed pool tenant(s) to delete.")

if count > 0:
    deleted, details = failed_qs.delete()
    print(f"Deleted {deleted} records: {details}")
else:
    print("Nothing to clean up.")

# Afficher l'état actuel du pool
pooled = Tenant.objects.filter(is_pool_tenant=True, status=TenantStatus.POOLED).count()
provisioning = Tenant.objects.filter(is_pool_tenant=True, status=TenantStatus.PROVISIONING).count()
print(f"Pool state after cleanup: {pooled} POOLED, {provisioning} PROVISIONING")
