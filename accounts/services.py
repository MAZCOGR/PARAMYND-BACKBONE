"""
accounts/services.py — Services for OTP via Email and SMS
M-04 fix : les fonctions retournent maintenant un booléen de succès
            pour que la vue puisse informer l'utilisateur en cas d'échec.
"""
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_otp_email(user, code) -> bool:
    """
    Envoie un OTP par email via SMTP (Postmark en prod, console en dev).
    Retourne True si l'envoi a réussi, False sinon.
    """
    subject = "Votre code de vérification Paramynd"
    message = (
        f"Bonjour {user.first_name or 'Utilisateur'},\n\n"
        f"Votre code de vérification est : {code}\n\n"
        f"Ce code expire dans 30 minutes.\n\n"
        f"L'équipe Paramynd."
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        logger.info(f"[EMAIL] Sent OTP to {user.email}")
        return True
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send OTP to {user.email}: {e}")
        return False


def send_phone_verification(phone: str) -> bool:
    """
    Envoie un OTP via Twilio Verify API (gère automatiquement le routage
    international, les tentatives, l'expiration et la conformité par pays).
    Retourne True si l'envoi a réussi, False sinon.
    """
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        verification = client.verify.v2 \
            .services(settings.TWILIO_VERIFY_SERVICE_SID) \
            .verifications \
            .create(to=phone, channel='sms')
        logger.info(f"[VERIFY] Sent to {phone}, status: {verification.status}")
        return True
    except Exception as e:
        logger.error(f"[VERIFY] Failed to send to {phone}: {e}")
        return False


def check_phone_verification(phone: str, code: str) -> tuple:
    """
    Vérifie un code OTP via Twilio Verify API.
    Retourne (approved: bool, error_message: str).
    Twilio gère nativement : expiration (10 min), brute-force (5 tentatives max).
    """
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        result = client.verify.v2 \
            .services(settings.TWILIO_VERIFY_SERVICE_SID) \
            .verification_checks \
            .create(to=phone, code=code)
        approved = result.status == 'approved'
        logger.info(f"[VERIFY] Check for {phone}: {result.status}")
        return approved, ''
    except Exception as e:
        logger.error(f"[VERIFY] Check failed for {phone}: {e}")
        # Codes Twilio Verify :
        # 60200 = code invalide, 60202 = expiré, 60203 = trop de renvois
        err_str = str(e)
        if '60200' in err_str:
            return False, "Code invalide. Vérifiez et réessayez."
        if '60202' in err_str:
            return False, "Le code a expiré. Demandez un nouveau code."
        if '60203' in err_str:
            return False, "Trop de tentatives de renvoi. Attendez quelques minutes."
        return False, "Erreur de vérification. Réessayez."


def send_otp_sms(phone, code) -> bool:
    """
    [LEGACY] Envoi SMS direct via Twilio (portée internationale limitée).
    Conservé comme fallback si TWILIO_VERIFY_SERVICE_SID n'est pas configuré.
    Utilise TWILIO_MESSAGING_SERVICE_SID si disponible, sinon TWILIO_FROM_NUMBER.
    """
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        messaging_service_sid = getattr(settings, 'TWILIO_MESSAGING_SERVICE_SID', None)
        if messaging_service_sid:
            msg = client.messages.create(
                body=f"Your Paramynd verification code: {code}. Expires in 30 minutes.",
                messaging_service_sid=messaging_service_sid,
                to=phone,
            )
        else:
            msg = client.messages.create(
                body=f"Your Paramynd verification code: {code}. Expires in 30 minutes.",
                from_=settings.TWILIO_FROM_NUMBER,
                to=phone,
            )
        logger.info(f"[SMS] Sent OTP to {phone}, SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"[SMS] Failed to send OTP to {phone}: {e}")
        return False
