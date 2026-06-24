import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def create_dns_record(subdomain: str, target: str) -> bool:
    """
    Crée un enregistrement CNAME sur Cloudflare.
    
    :param subdomain: Le sous-domaine complet (ex: "dali.paramynd.com")
    :param target: La cible (ex: "ghs.googlehosted.com.")
    :return: True si succès ou si l'enregistrement existe déjà, False sinon.
    """
    token = settings.CLOUDFLARE_API_TOKEN
    zone_id = settings.CLOUDFLARE_ZONE_ID
    
    if not token or not zone_id:
        logger.warning(f"Cloudflare API Token ou Zone ID manquant. Impossible de créer le DNS pour {subdomain}.")
        return False
        
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "type": "CNAME",
        "name": subdomain,
        "content": target,
        "ttl": 1,          # 1 = Auto
        "proxied": False   # IMPORTANT: Doit être False pour que Google Cloud Run valide le domaine
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            logger.info(f"Cloudflare DNS créé avec succès: {subdomain} -> {target}")
            return True
            
        # Cloudflare renvoie l'erreur 81053 ou 81057 si l'enregistrement existe déjà
        errors = data.get("errors", [])
        for err in errors:
            code = err.get("code")
            if code in [81053, 81057]:
                logger.info(f"Cloudflare DNS existe déjà pour {subdomain}.")
                return True
                
        logger.error(f"Erreur Cloudflare API: {errors}")
        return False
        
    except Exception as e:
        logger.error(f"Erreur de connexion à Cloudflare API: {e}")
        return False
