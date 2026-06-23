"""
accounts/services.py — Services for OTP via Email and SMS
"""
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_email(user, code):
    """
    Sends an OTP via Email using Postmark SMTP (configured in settings).
    """
    subject = "Votre code de vérification Paramynd"
    message = f"Bonjour {user.first_name or 'Utilisateur'},\n\nVotre code de vérification est : {code}\n\nL'équipe Paramynd."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        logger.info(f"[EMAIL] Sent OTP to {user.email}")
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send OTP to {user.email}: {e}")

def send_otp_sms(phone, code):
    """
    Sends an OTP via SMS using Twilio SDK.
    """
    try:
        # Import local pour ne pas bloquer si twilio n'est pas encore installé
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=f"Votre code de vérification Paramynd : {code}",
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone
        )
        logger.info(f"[SMS] Sent OTP to {phone}, SID: {msg.sid}")
    except Exception as e:
        logger.error(f"[SMS] Failed to send OTP to {phone}: {e}")
