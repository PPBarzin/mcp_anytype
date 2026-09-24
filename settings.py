import os
from pydantic_settings import BaseSettings

# --- 1. On ajoute la fonction pour lire les secrets/variables d'environnement ---
def get_secret(secret_name: str, default_value: str = None) -> str | None:
    """
    Lit un secret depuis le chemin standard de Docker Secrets (/run/secrets/).
    En fallback, si le fichier n'existe pas, lit une variable d'environnement.
    """
    secret_path = f'/run/secrets/{secret_name}'
    if os.path.exists(secret_path):
        try:
            with open(secret_path, 'r', encoding='utf-8') as secret_file:
                return secret_file.read().strip()
        except IOError:
            return default_value
    # Si le chemin du secret n'existe pas, on cherche une variable d'environnement
    return os.getenv(secret_name.upper(), default_value)

# --- 2. On définit la classe de configuration ---
class Settings(BaseSettings):
    anytype_api_url: str
    anytype_auth_token: str
    anytype_version: str

# --- 3. On initialise la configuration en utilisant notre nouvelle fonction ---
# Les valeurs par défaut sont celles extraites de votre configuration,
# mais il est fortement recommandé de les définir via des variables d'environnement.
api_url = get_secret('ANYTYPE_API_URL', 'http://localhost:31009')
auth_token = get_secret('ANYTYPE_AUTH_TOKEN')
version = get_secret('ANYTYPE_VERSION', '2025-11-08')

if not auth_token or not api_url or not version:
    raise ValueError("ERREUR: ANYTYPE_API_URL, ANYTYPE_AUTH_TOKEN, et ANYTYPE_VERSION doivent être définis, soit via des secrets Docker, soit via des variables d'environnement.")

settings = Settings(
    anytype_api_url=api_url,
    anytype_auth_token=auth_token,
    anytype_version=version
)

print("Configuration pour Anytype chargée avec succès.")
