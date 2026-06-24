from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.contrib import messages
from accounts.services import send_otp_email, send_otp_sms
from tenants.models import Tenant
import re

User = get_user_model()

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
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        company = request.POST.get('company', '')
        password = request.POST.get('password', '')
        
        # Simple validation
        if User.objects.filter(email=email).exists():
            messages.error(request, "Un compte avec cet email existe déjà.")
            return render(request, 'request_demo.html')
            
        # Create user (inactive until OTP)
        email_code = get_random_string(length=6, allowed_chars='0123456789')
        phone_code = get_random_string(length=6, allowed_chars='0123456789')
        
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
            phone_verification_code=phone_code
        )
        
        # Store company + password in session to create Tenant later
        request.session['pending_company'] = company
        request.session['pending_user_id'] = user.id
        request.session['pending_password'] = password  # Needed for createsuperuser
        
        # Send OTPs
        send_otp_email(user, email_code)
        send_otp_sms(phone, phone_code)
        
        return redirect('verify_otp')
        
    return render(request, 'request_demo.html')

def verify_otp_view(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('request_demo')
        
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify_email':
            code = request.POST.get('email_code')
            if code and code == user.email_verification_code:
                user.email_verified = True
                user.email_verification_code = None
                user.save(update_fields=['email_verified', 'email_verification_code'])
            else:
                messages.error(request, "Code email invalide.")
                
        elif action == 'verify_sms':
            code = request.POST.get('sms_code')
            if code and code == user.phone_verification_code:
                user.phone_verified = True
                user.phone_verification_code = None
                user.save(update_fields=['phone_verified', 'phone_verification_code'])
            else:
                messages.error(request, "Code SMS invalide.")
                
        elif action == 'resend_email':
            user.email_verification_code = get_random_string(length=6, allowed_chars='0123456789')
            user.save(update_fields=['email_verification_code'])
            send_otp_email(user, user.email_verification_code)
            messages.success(request, "Nouveau code email envoyé.")
            
        elif action == 'resend_sms':
            user.phone_verification_code = get_random_string(length=6, allowed_chars='0123456789')
            user.save(update_fields=['phone_verification_code'])
            send_otp_sms(user.phone_number, user.phone_verification_code)
            messages.success(request, "Nouveau code SMS envoyé.")
            
        # Check if fully verified
        if user.email_verified and user.phone_verified:
            user.is_active = True
            user.save(update_fields=['is_active'])
            
            # Create Tenant automatically
            company = request.session.get('pending_company', '')
            # Récupérer le mot de passe en session pour le createsuperuser
            admin_password = request.session.get('pending_password', '')
            final_slug = ''
            tenant = None

            if company:
                import unicodedata
                base_slug = unicodedata.normalize('NFKD', company).encode('ascii', 'ignore').decode('ascii').lower()
                slug = re.sub(r'[^a-z0-9-]+', '-', base_slug).strip('-')
                slug = re.sub(r'-+', '-', slug)[:28]
                if len(slug) < 3:
                    slug = f"t-{user.id}"[:30]

                # Garantir min 3 chars avec suffixe si besoin
                if len(slug) < 3:
                    slug = slug + 'co'
                    
                # Handle slug collision
                original_slug = slug
                counter = 1
                while Tenant.objects.filter(slug=slug).exists():
                    slug = f"{original_slug[:25]}-{counter}"
                    counter += 1
                
                db_name = slug.replace('-', '_')
                final_slug = slug
                
                tenant = Tenant.objects.create(
                    name=company,
                    slug=slug,
                    contact_email=user.email,
                    db_name=db_name,
                    gcp_project_id='yellow-455523',
                    cloud_run_region='europe-west9',
                    cloud_sql_instance='yellow-455523:europe-west9:yellow-db-paris',
                )
            
            # Clean session
            tenant_id = str(tenant.id) if tenant else None
            del request.session['pending_user_id']
            for key in ['pending_company', 'pending_password']:
                if key in request.session:
                    del request.session[key]

            # ── Lancer le provisioning automatique en background ──────────
            if tenant_id and admin_password:
                import threading
                from tenants.services.provisioning import provision_tenant
                t = threading.Thread(
                    target=provision_tenant,
                    args=(tenant_id, user.email, admin_password),
                    daemon=True,
                    name=f'provision-{final_slug}',
                )
                t.start()
                
            messages.success(request, "Votre compte et votre espace client ont été créés avec succès !")
            if final_slug:
                return redirect(f'/building-workspace/?slug={final_slug}')
            return redirect('building_workspace')
            
    return render(request, 'verify_otp.html', {'user': user})

