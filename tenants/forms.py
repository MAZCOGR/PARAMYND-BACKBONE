"""
tenants/forms.py — Formulaires Django pour la gestion des tenants
"""
from django import forms
from .models import Tenant, TenantStatus


class TenantCreateForm(forms.ModelForm):
    """Formulaire de création d'un tenant."""

    admin_password = forms.CharField(
        label="Mot de passe admin",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'id': 'id_admin_password', 'placeholder': '••••••••'}),
        required=True,
        help_text="Mot de passe initial pour le compte administrateur du tenant."
    )
    admin_password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'id': 'id_admin_password_confirm', 'placeholder': '••••••••'}),
        required=True
    )

    class Meta:
        model = Tenant
        fields = [
            'name', 'slug', 'contact_email',
            'admin_password', 'admin_password_confirm',
            'gcp_project_id', 'cloud_run_region',
            'cloud_sql_instance', 'db_name',
            'custom_domain', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Acme Corp', 'class': 'form-input'}),
            'slug': forms.TextInput(attrs={'placeholder': 'acme-corp', 'class': 'form-input'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'contact@acme.com', 'class': 'form-input'}),
            'gcp_project_id': forms.TextInput(attrs={'class': 'form-input'}),
            'cloud_run_region': forms.TextInput(attrs={'class': 'form-input'}),
            'cloud_sql_instance': forms.TextInput(attrs={'placeholder': 'project:region:instance', 'class': 'form-input'}),
            'db_name': forms.TextInput(attrs={'placeholder': 'paramynd_acme', 'class': 'form-input'}),
            'custom_domain': forms.TextInput(attrs={'placeholder': 'acme.paramynd.com', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'placeholder': 'Notes internes...'}),
        }
        help_texts = {
            'slug': 'Minuscules, tirets autorisés, 3-30 caractères. Ex: acme-corp',
            'cloud_sql_instance': 'Laissez vide pour utiliser l\'instance par défaut',
            'db_name': 'Laissez vide pour générer automatiquement depuis le slug',
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '')
        import re
        if not re.match(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$', slug):
            raise forms.ValidationError(
                "Le slug doit être en minuscules, alphanumérique avec tirets, 3-30 caractères."
            )
        return slug

    def clean_db_name(self):
        db_name = self.cleaned_data.get('db_name', '')
        if not db_name:
            slug = self.cleaned_data.get('slug', '')
            return slug.replace('-', '_')
        return db_name


class TenantUpdateForm(forms.ModelForm):
    """Formulaire de modification d'un tenant."""

    class Meta:
        model = Tenant
        fields = [
            'name', 'contact_email', 'status',
            'custom_domain', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'custom_domain': forms.TextInput(attrs={'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }


class DeployForm(forms.Form):
    """Formulaire de déploiement d'un tenant."""
    image_tag = forms.ChoiceField(
        label='Version à déployer',
        widget=forms.Select(attrs={'class': 'form-input'}),
        choices=[],
    )
    min_instances = forms.IntegerField(
        label='Instances min.',
        initial=0,
        min_value=0,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 10}),
    )
    max_instances = forms.IntegerField(
        label='Instances max.',
        initial=10,
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 100}),
    )
    memory = forms.ChoiceField(
        label='Mémoire',
        choices=[('256Mi', '256 Mi'), ('512Mi', '512 Mi'), ('1Gi', '1 Gi'), ('2Gi', '2 Gi')],
        initial='512Mi',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    cpu = forms.ChoiceField(
        label='CPU',
        choices=[('1', '1 vCPU'), ('2', '2 vCPU'), ('4', '4 vCPU')],
        initial='1',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )

    def __init__(self, *args, available_tags=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_tags:
            self.fields['image_tag'].choices = [
                (tag['tag'], f"{tag['tag']} — {tag['uri']}")
                for tag in available_tags
            ]
