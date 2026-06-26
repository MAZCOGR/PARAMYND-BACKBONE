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


def send_otp_sms(phone, code) -> bool:
    """
    Envoie un OTP par SMS via Twilio SDK.
    Retourne True si l'envoi a réussi, False sinon.
    """
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=f"Votre code de vérification Paramynd : {code}. Ce code expire dans 30 minutes.",
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone
        )
        logger.info(f"[SMS] Sent OTP to {phone}, SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"[SMS] Failed to send OTP to {phone}: {e}")
        return False
