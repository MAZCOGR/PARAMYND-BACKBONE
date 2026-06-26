from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import UserAdminCreationForm, UserAdminChangeForm

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
@user_passes_test(is_admin)
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/users/list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_create_view(request):
    if request.method == 'POST':
        form = UserAdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur {user.email} créé avec succès.")
            return redirect('accounts:user_list')
    else:
        form = UserAdminCreationForm()
    return render(request, 'accounts/users/form.html', {'form': form, 'title': 'Créer un utilisateur'})

@login_required
@user_passes_test(is_admin)
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserAdminChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Utilisateur {user.email} mis à jour.")
            return redirect('accounts:user_list')
    else:
        form = UserAdminChangeForm(instance=user)
    return render(request, 'accounts/users/form.html', {'form': form, 'title': 'Modifier l\'utilisateur', 'user_obj': user})

@login_required
@user_passes_test(is_admin)
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        else:
            user.delete()
            messages.success(request, f"Utilisateur {user.email} supprimé.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/users/confirm_delete.html', {'user_obj': user})

@login_required
@user_passes_test(is_admin)
def user_password_reset_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        # N-02 fix : valider la longueur minimum du mot de passe
        if not new_password:
            messages.error(request, "Le mot de passe ne peut pas être vide.")
        elif len(new_password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, f"Mot de passe de {user.email} réinitialisé.")
            return redirect('accounts:user_list')
    return render(request, 'accounts/users/password_reset.html', {'user_obj': user})

from django.contrib.auth.models import Group
from .models import GroupAccess

@login_required
def role_matrix_view(request):
    """Vue pour gérer la matrice dynamique des droits (RBAC)."""
    # Seuls les superadmins peuvent modifier la matrice
    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'superadmin') or request.user.groups.filter(name='Super Admin').exists()):
        messages.error(request, "Accès refusé.")
        return redirect('accounts:user_list')

    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "add_group":
            new_group_name = request.POST.get('new_group_name', '').strip()
            if new_group_name:
                if not Group.objects.filter(name__iexact=new_group_name).exists():
                    group = Group.objects.create(name=new_group_name)
                    GroupAccess.objects.create(group=group)
                    messages.success(request, f"Le rôle '{new_group_name}' a été créé.")
                else:
                    messages.error(request, f"Un rôle avec ce nom existe déjà.")
            
        elif action == "save_matrix":
            groups = Group.objects.all()
            for group in groups:
                if group.name == 'Super Admin': continue
                
                access, created = GroupAccess.objects.get_or_create(group=group)
                
                access.can_access_tenants = request.POST.get(f'tenants_{group.id}') == 'on'
                access.can_access_builds = request.POST.get(f'builds_{group.id}') == 'on'
                access.can_access_monitoring = request.POST.get(f'monitoring_{group.id}') == 'on'
                access.can_access_users = request.POST.get(f'users_{group.id}') == 'on'
                access.can_access_roles = request.POST.get(f'roles_{group.id}') == 'on'
                access.save()
            
            messages.success(request, "La matrice des droits a été mise à jour.")
            
        return redirect('accounts:role_matrix')

    groups = Group.objects.exclude(name='Super Admin').order_by('id')
    for group in groups:
        GroupAccess.objects.get_or_create(group=group)

    context = {
        'groups': groups,
        'title': 'Matrice des Rôles',
    }
    return render(request, 'accounts/roles/matrix.html', context)
