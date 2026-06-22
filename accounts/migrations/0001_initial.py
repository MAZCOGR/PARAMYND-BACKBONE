from django.db import migrations, models
import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('first_name', models.CharField(blank=True, max_length=100, verbose_name='Prénom')),
                ('last_name', models.CharField(blank=True, max_length=100, verbose_name='Nom')),
                ('role', models.CharField(choices=[('superadmin', 'Super Administrateur'), ('admin', 'Administrateur'), ('manager', 'Manager'), ('viewer', 'Observateur')], default='viewer', max_length=20, verbose_name='Rôle')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff Django')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date d'inscription")),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='Dernière connexion')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('notes', models.TextField(blank=True, verbose_name='Notes internes')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Utilisateur',
                'verbose_name_plural': 'Utilisateurs',
                'db_table': 'accounts_user',
                'ordering': ['-date_joined'],
            },
            managers=[
                ('objects', django.contrib.auth.models.BaseUserManager()),
            ],
        ),
    ]
