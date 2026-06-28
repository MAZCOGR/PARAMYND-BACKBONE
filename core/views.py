"""
core/views.py — Vues publiques : landing page, request_demo, verify_otp, building_workspace
"""
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
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

        # Bug #14 fix : régénérer le session ID après create_user() pour
        # prévenir la fixation de session (session fixation attack).
        # Django ne le fait automatiquement qu'après login(), pas create_user().
        request.session.cycle_key()

        # Bug #5 fix : tenter les envois OTP APRÈS avoir créé l'utilisateur.
        # Si les DEUX envois échouent → supprimer l'utilisateur pour éviter
        # qu'il soit bloqué définitivement (ni activation ni ré-inscription possible).
        email_sent = send_otp_email(user, email_code)
        sms_sent = send_otp_sms(phone, phone_code)

        if not email_sent and not sms_sent:
            user.delete()
            messages.error(
                request,
                "Impossible d'envoyer les codes de vérification (email et SMS). "
                "Vérifiez vos coordonnées ou contactez le support."
            )
            return render(request, 'request_demo.html')

        # Stocker les infos de session (sans le password — C-04 fix)
        request.session['pending_company'] = company
        request.session['pending_user_id'] = user.id

        # M-04 fix : informer l'utilisateur si un seul envoi a échoué
        if not email_sent:
            messages.warning(request, "L'email de vérification n'a pas pu être envoyé. Vérifiez votre adresse email.")
        if not sms_sent:
            messages.warning(request, "Le SMS de vérification n'a pas pu être envoyé. Vérifiez votre numéro.")

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

        # Bug #12 fix : limiter les tentatives OTP (max 5) pour éviter le brute-force
        MAX_OTP_ATTEMPTS = 5

        if action == 'verify_email':
            code = request.POST.get('email_code', '').strip()
            # H-06 fix : vérifier l'expiration de l'OTP
            if user.otp_email_expires_at and now > user.otp_email_expires_at:
                messages.error(request, "Le code email a expiré. Veuillez en demander un nouveau.")
            elif user.otp_attempts >= MAX_OTP_ATTEMPTS:
                messages.error(
                    request,
                    f"Trop de tentatives ({MAX_OTP_ATTEMPTS} max). Demandez un nouveau code."
                )
            elif code and code == user.email_verification_code:
                user.email_verified = True
                user.email_verification_code = None
                user.otp_email_expires_at = None
                user.otp_attempts = 0  # Réinitialiser après succès
                user.save(update_fields=['email_verified', 'email_verification_code', 'otp_email_expires_at', 'otp_attempts'])
                messages.success(request, "Email vérifié avec succès.")
            else:
                user.otp_attempts = (user.otp_attempts or 0) + 1
                user.save(update_fields=['otp_attempts'])
                remaining = max(0, MAX_OTP_ATTEMPTS - user.otp_attempts)
                messages.error(request, f"Code email invalide. {remaining} tentative(s) restante(s).")

        elif action == 'verify_sms':
            code = request.POST.get('sms_code', '').strip()
            # H-06 fix : vérifier l'expiration de l'OTP
            if user.otp_phone_expires_at and now > user.otp_phone_expires_at:
                messages.error(request, "Le code SMS a expiré. Veuillez en demander un nouveau.")
            elif user.otp_attempts >= MAX_OTP_ATTEMPTS:
                messages.error(
                    request,
                    f"Trop de tentatives ({MAX_OTP_ATTEMPTS} max). Demandez un nouveau code."
                )
            elif code and code == user.phone_verification_code:
                user.phone_verified = True
                user.phone_verification_code = None
                user.otp_phone_expires_at = None
                user.otp_attempts = 0  # Réinitialiser après succès
                user.save(update_fields=['phone_verified', 'phone_verification_code', 'otp_phone_expires_at', 'otp_attempts'])
                messages.success(request, "Téléphone vérifié avec succès.")
            else:
                user.otp_attempts = (user.otp_attempts or 0) + 1
                user.save(update_fields=['otp_attempts'])
                remaining = max(0, MAX_OTP_ATTEMPTS - user.otp_attempts)
                messages.error(request, f"Code SMS invalide. {remaining} tentative(s) restante(s).")

        elif action == 'resend_email':
            new_code = get_random_string(length=6, allowed_chars='0123456789')
            new_expiry = timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)
            user.email_verification_code = new_code
            user.otp_email_expires_at = new_expiry
            user.otp_attempts = 0  # Réinitialiser les tentatives après renvoi
            user.save(update_fields=['email_verification_code', 'otp_email_expires_at', 'otp_attempts'])
            if send_otp_email(user, new_code):
                messages.success(request, "Nouveau code email envoyé.")
            else:
                messages.error(request, "Impossible d'envoyer le code email. Réessayez plus tard.")

        elif action == 'resend_sms':
            # Bug #13 fix : vérifier que le numéro de téléphone est bien renseigné
            if not user.phone_number or not user.phone_number.strip():
                messages.error(
                    request,
                    "Aucun numéro de téléphone associé à votre compte. "
                    "Contactez le support pour le mettre à jour."
                )
            else:
                new_code = get_random_string(length=6, allowed_chars='0123456789')
                new_expiry = timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)
                user.phone_verification_code = new_code
                user.otp_phone_expires_at = new_expiry
                user.otp_attempts = 0  # Réinitialiser les tentatives après renvoi
                user.save(update_fields=['phone_verification_code', 'otp_phone_expires_at', 'otp_attempts'])
                if send_otp_sms(user.phone_number, new_code):
                    messages.success(request, "Nouveau code SMS envoyé.")
                else:
                    messages.error(request, "Impossible d'envoyer le SMS. Réessayez plus tard.")

        # Recharger l'utilisateur après les saves
        user.refresh_from_db()

        # Bug #4 fix : vérifier si entièrement vérifié avec un verrou transactionnel
        # pour éviter la race condition (double-clic → double provisioning GCP).
        if user.email_verified and user.phone_verified and not user.is_active:
            with transaction.atomic():
                # Re-lire avec verrou exclusif pour éviter toute exécution parallèle
                locked_user = User.objects.select_for_update().get(id=user_id)

                if locked_user.is_active:
                    # Déjà activé par une requête parallèle — rediriger proprement
                    pending_slug = request.session.get('pending_slug', '')
                    request.session.pop('pending_user_id', None)
                    request.session.pop('pending_company', None)
                    request.session.pop('pending_slug', None)
                    return redirect(f'/building-workspace/?slug={pending_slug}')

                locked_user.is_active = True
                locked_user.save(update_fields=['is_active'])

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
                        slug = f"t-{str(locked_user.id)[:8]}"

                    original_slug = slug
                    counter = 1

                    # H-09 fix : savepoints imbriqués pour gérer l'IntegrityError
                    # SANS corrompre la transaction parente (PostgreSQL exige
                    # un ROLLBACK TO SAVEPOINT après toute erreur SQL).
                    from django.db import IntegrityError
                    db_name = slug.replace('-', '_')
                    final_slug = slug

                    try:
                        with transaction.atomic():  # savepoint #1
                            tenant = Tenant.objects.create(
                                name=company,
                                slug=slug,
                                contact_email=locked_user.email,
                                db_name=db_name,
                                gcp_project_id='yellow-455523',
                                cloud_run_region='europe-west9',
                                cloud_sql_instance='yellow-455523:europe-west9:yellow-db-paris',
                            )
                    except IntegrityError:
                        # Slug déjà pris : générer un suffixe unique
                        tenant = None
                        while counter <= 10:
                            slug = f"{original_slug[:25]}-{counter}"
                            counter += 1
                            db_name = slug.replace('-', '_')
                            final_slug = slug
                            try:
                                with transaction.atomic():  # savepoint #N
                                    tenant = Tenant.objects.create(
                                        name=company,
                                        slug=slug,
                                        contact_email=locked_user.email,
                                        db_name=db_name,
                                        gcp_project_id='yellow-455523',
                                        cloud_run_region='europe-west9',
                                        cloud_sql_instance='yellow-455523:europe-west9:yellow-db-paris',
                                    )
                                break  # succès
                            except IntegrityError:
                                continue
                        if tenant is None:
                            messages.error(request, "Impossible de créer l'espace. Contactez le support.")
                            return render(request, 'verify_otp.html', {'user': locked_user})

                # Stocker le slug pour la redirection (en cas de double-clic)
                request.session['pending_slug'] = final_slug

                # Nettoyer la session
                tenant_id = str(tenant.id) if tenant else None
                request.session.pop('pending_user_id', None)
                request.session.pop('pending_company', None)

                # Lancer le provisioning en background
                # C-04 fix : un mot de passe temporaire aléatoire est généré pour le superuser
                # du tenant (jamais le mot de passe réel de l'utilisateur).
                if tenant_id:
                    import threading
                    from tenants.services.provisioning import provision_tenant
                    import secrets
                    temp_password = secrets.token_urlsafe(16)
                    t = threading.Thread(
                        target=provision_tenant,
                        args=(tenant_id, locked_user.email, temp_password),
                        daemon=False,  # BUG-D03 fix : daemon=True tuerait le thread si Cloud Run scale-to-zero
                        name=f'provision-{final_slug}',
                    )
                    t.start()

                messages.success(request, "Votre compte et votre espace client ont été créés avec succès !")
                request.session.pop('pending_slug', None)
                if final_slug:
                    return redirect(f'/building-workspace/?slug={final_slug}')
                return redirect('building_workspace')

    return render(request, 'verify_otp.html', {'user': user})
