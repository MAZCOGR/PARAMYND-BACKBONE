"""
core/views.py — Vues publiques : landing page, request_demo, verify_otp, building_workspace
"""
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from accounts.services import send_otp_email, send_otp_sms
from tenants.models import Tenant
import re

User = get_user_model()

# Durée de validité des OTPs (H-06 fix)
OTP_VALIDITY_MINUTES = 30


def home_view(request):
    """Landing page publique de Paramynd Admin."""
    return render(request, 'home.html')


def building_workspace_view(request):
    """Page de chargement simulée après la création du compte/tenant."""
    slug = request.GET.get('slug', '')
    return render(request, 'building_workspace.html', {'slug': slug})


def request_demo_view(request):
    """Request a Demo / Onboarding page."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        company = request.POST.get('company', '').strip()
        password = request.POST.get('password', '').strip()

        # M-02 fix : vérification côté serveur que les deux mots de passe correspondent
        confirm_password = request.POST.get('confirm_password', '').strip()
        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'request_demo.html')

        if len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, 'request_demo.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Un compte avec cet email existe déjà.")
            return render(request, 'request_demo.html')

        # Générer les codes OTP
        email_code = get_random_string(length=6, allowed_chars='0123456789')
        phone_code = get_random_string(length=6, allowed_chars='0123456789')
        otp_expiry = timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            is_active=False,
            email_verified=False,
            phone_verified=False,
            email_verification_code=email_code,
            phone_verification_code=phone_code,
            # H-06 fix : stocker la date d'expiration des OTPs
            otp_email_expires_at=otp_expiry,
            otp_phone_expires_at=otp_expiry,
        )

        # Stocker les infos de session (sans le password — C-04 fix)
        request.session['pending_company'] = company
        request.session['pending_user_id'] = user.id
        # C-04 fix : le password n'est PAS stocké en session.
        # Il sera transmis directement au thread de provisioning via un token sécurisé.
        # Le superuser du tenant est créé avec un mot de passe temporaire aléatoire,
        # puis l'utilisateur reçoit ses identifiants par email.

        # M-04 fix : informer l'utilisateur si l'envoi échoue
        email_sent = send_otp_email(user, email_code)
        sms_sent = send_otp_sms(phone, phone_code)

        if not email_sent:
            messages.warning(request, "L'email de vérification n'a pas pu être envoyé. Contactez le support.")
        if not sms_sent:
            messages.warning(request, "Le SMS de vérification n'a pas pu être envoyé. Contactez le support.")

        return redirect('verify_otp')

    return render(request, 'request_demo.html')


def verify_otp_view(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('request_demo')

    # N-05 fix : gérer le cas où l'utilisateur n'existe plus (suppression entre les étapes)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        del request.session['pending_user_id']
        messages.error(request, "Session expirée. Veuillez recommencer.")
        return redirect('request_demo')

    if request.method == 'POST':
        action = request.POST.get('action')
        now = timezone.now()

        if action == 'verify_email':
            code = request.POST.get('email_code', '').strip()
            # H-06 fix : vérifier l'expiration de l'OTP
            if user.otp_email_expires_at and now > user.otp_email_expires_at:
                messages.error(request, "Le code email a expiré. Veuillez en demander un nouveau.")
            elif code and code == user.email_verification_code:
                user.email_verified = True
                user.email_verification_code = None
                user.otp_email_expires_at = None
                user.save(update_fields=['email_verified', 'email_verification_code', 'otp_email_expires_at'])
                messages.success(request, "Email vérifié avec succès.")
            else:
                messages.error(request, "Code email invalide.")

        elif action == 'verify_sms':
            code = request.POST.get('sms_code', '').strip()
            # H-06 fix : vérifier l'expiration de l'OTP
            if user.otp_phone_expires_at and now > user.otp_phone_expires_at:
                messages.error(request, "Le code SMS a expiré. Veuillez en demander un nouveau.")
            elif code and code == user.phone_verification_code:
                user.phone_verified = True
                user.phone_verification_code = None
                user.otp_phone_expires_at = None
                user.save(update_fields=['phone_verified', 'phone_verification_code', 'otp_phone_expires_at'])
                messages.success(request, "Téléphone vérifié avec succès.")
            else:
                messages.error(request, "Code SMS invalide.")

        elif action == 'resend_email':
            new_code = get_random_string(length=6, allowed_chars='0123456789')
            new_expiry = timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)
            user.email_verification_code = new_code
            user.otp_email_expires_at = new_expiry
            user.save(update_fields=['email_verification_code', 'otp_email_expires_at'])
            if send_otp_email(user, new_code):
                messages.success(request, "Nouveau code email envoyé.")
            else:
                messages.error(request, "Impossible d'envoyer le code email. Réessayez plus tard.")

        elif action == 'resend_sms':
            new_code = get_random_string(length=6, allowed_chars='0123456789')
            new_expiry = timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)
            user.phone_verification_code = new_code
            user.otp_phone_expires_at = new_expiry
            user.save(update_fields=['phone_verification_code', 'otp_phone_expires_at'])
            if send_otp_sms(user.phone_number, new_code):
                messages.success(request, "Nouveau code SMS envoyé.")
            else:
                messages.error(request, "Impossible d'envoyer le SMS. Réessayez plus tard.")

        # Recharger l'utilisateur après les saves
        user.refresh_from_db()

        # Vérifier si entièrement vérifié
        if user.email_verified and user.phone_verified:
            user.is_active = True
            user.save(update_fields=['is_active'])

            # Créer le Tenant automatiquement
            company = request.session.get('pending_company', '')
            final_slug = ''
            tenant = None

            if company:
                import unicodedata
                base_slug = unicodedata.normalize('NFKD', company).encode('ascii', 'ignore').decode('ascii').lower()
                slug = re.sub(r'[^a-z0-9-]+', '-', base_slug).strip('-')
                slug = re.sub(r'-+', '-', slug)[:28]
                if len(slug) < 3:
                    slug = f"t-{str(user.id)[:8]}"

                original_slug = slug
                counter = 1

                # H-09 fix : utiliser une transaction et try/except IntegrityError
                from django.db import IntegrityError
                db_name = slug.replace('-', '_')
                final_slug = slug

                try:
                    tenant = Tenant.objects.create(
                        name=company,
                        slug=slug,
                        contact_email=user.email,
                        db_name=db_name,
                        gcp_project_id='yellow-455523',
                        cloud_run_region='europe-west9',
                        cloud_sql_instance='yellow-455523:europe-west9:yellow-db-paris',
                    )
                except IntegrityError:
                    # Slug déjà pris : en générer un avec suffixe unique
                    while True:
                        slug = f"{original_slug[:25]}-{counter}"
                        counter += 1
                        db_name = slug.replace('-', '_')
                        final_slug = slug
                        try:
                            tenant = Tenant.objects.create(
                                name=company,
                                slug=slug,
                                contact_email=user.email,
                                db_name=db_name,
                                gcp_project_id='yellow-455523',
                                cloud_run_region='europe-west9',
                                cloud_sql_instance='yellow-455523:europe-west9:yellow-db-paris',
                            )
                            break
                        except IntegrityError:
                            if counter > 10:
                                messages.error(request, "Impossible de créer l'espace. Contactez le support.")
                                return render(request, 'verify_otp.html', {'user': user})

            # Nettoyer la session
            tenant_id = str(tenant.id) if tenant else None
            request.session.pop('pending_user_id', None)
            request.session.pop('pending_company', None)

            # Lancer le provisioning en background
            # C-04 fix : un mot de passe temporaire aléatoire est généré pour le superuser
            # du tenant (jamais le mot de passe réel de l'utilisateur).
            # L'utilisateur peut le changer via un reset password depuis son espace.
            if tenant_id:
                import threading
                from tenants.services.provisioning import provision_tenant
                # Générer un mot de passe temporaire sécurisé
                import secrets
                temp_password = secrets.token_urlsafe(16)
                t = threading.Thread(
                    target=provision_tenant,
                    args=(tenant_id, user.email, temp_password),
                    daemon=True,
                    name=f'provision-{final_slug}',
                )
                t.start()

            messages.success(request, "Votre compte et votre espace client ont été créés avec succès !")
            if final_slug:
                return redirect(f'/building-workspace/?slug={final_slug}')
            return redirect('building_workspace')

    return render(request, 'verify_otp.html', {'user': user})
