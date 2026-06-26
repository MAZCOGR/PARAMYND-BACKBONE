from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class UserAdminCreationForm(forms.ModelForm):
    """
    Formulaire de création d'un utilisateur admin.
    N-03 fix : le champ password a maintenant une validation de longueur minimum.
    """
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput,
        min_length=8,
        help_text='8 caractères minimum.',
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Rôles / Accès (Groupes)'
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'phone_number', 'is_active', 'groups')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # N-01 fix : is_staff uniquement si le rôle le justifie
        # (admin ou superadmin) — pas hardcodé à True pour tous
        user.is_staff = user.role in ('admin', 'superadmin')
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Rôles / Accès (Groupes)'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'is_active', 'groups')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
            self.save_m2m()
        return user
