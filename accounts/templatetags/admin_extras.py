from django import template

register = template.Library()

@register.filter(name='has_module_access')
def has_module_access(user, module_name):
    """Vérifie si l'utilisateur appartient à un groupe qui a l'accès à ce module."""
    if not user.is_authenticated:
        return False
        
    # S'il est superadmin ou si son ancien champ role est SUPERADMIN
    if user.is_superuser or (hasattr(user, 'role') and user.role == 'superadmin'):
        return True
        
    # Vérifie si le groupe "Super Admin" lui est assigné
    if user.groups.filter(name='Super Admin').exists():
        return True
    
    attr_name = f"can_access_{module_name}"
    for group in user.groups.all():
        if hasattr(group, 'access') and getattr(group.access, attr_name, False):
            return True
            
    # Fallback legacy basé sur l'ancien champ 'role' s'il n'a pas de groupe
    if not user.groups.exists() and hasattr(user, 'role'):
        if user.role == 'admin':
            return True # Admins ont accès à tout
        if user.role == 'manager':
            # Managers peuvent voir Tenants et Monitoring, mais pas Users ni Roles
            if module_name in ['tenants', 'monitoring']:
                return True
        if user.role == 'viewer':
            if module_name in ['tenants']: # Exemple : Viewer ne voit que Tenants
                return True

    return False
