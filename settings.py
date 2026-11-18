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
    # --- Sécurité de l'exposition réseau ---
    mcp_host: str = "127.0.0.1"
    # Listes séparées par des virgules (str et non list : pydantic-settings exigerait du JSON dans l'env)
    mcp_allowed_hosts: str = ""
    mcp_allowed_origins: str = ""
    enable_auth_tools: bool = False

# --- 3. On initialise la configuration en utilisant notre nouvelle fonction ---
# Les valeurs par défaut sont celles extraites de votre configuration,
# mais il est fortement recommandé de les définir via des variables d'environnement.
api_url = get_secret('ANYTYPE_API_URL', 'http://localhost:31009')
auth_token = get_secret('ANYTYPE_AUTH_TOKEN')
version = get_secret('ANYTYPE_VERSION', '2025-11-08')

if not auth_token or not api_url or not version:
    raise ValueError("ERREUR: ANYTYPE_API_URL, ANYTYPE_AUTH_TOKEN, et ANYTYPE_VERSION doivent être définis, soit via des secrets Docker, soit via des variables d'environnement.")

# Écoute en loopback par défaut : le serveur ne doit pas être joignable depuis le réseau.
mcp_host = get_secret('MCP_HOST', '127.0.0.1')
# Protection DNS rebinding : seuls ces en-têtes Host/Origin sont acceptés sur /sse et /mcp.
mcp_allowed_hosts = get_secret('MCP_ALLOWED_HOSTS', '127.0.0.1:*,localhost:*')
mcp_allowed_origins = get_secret('MCP_ALLOWED_ORIGINS', 'http://127.0.0.1:*,http://localhost:*')
# create-auth-challenge / create-api-key désactivés par défaut : un agent ne doit pas pouvoir générer de clé API.
enable_auth_tools = (get_secret('ANYTYPE_MCP_ENABLE_AUTH_TOOLS', 'false') or '').lower() in ('1', 'true', 'yes')

settings = Settings(
    anytype_api_url=api_url,
    anytype_auth_token=auth_token,
    anytype_version=version,
    mcp_host=mcp_host,
    mcp_allowed_hosts=mcp_allowed_hosts,
    mcp_allowed_origins=mcp_allowed_origins,
    enable_auth_tools=enable_auth_tools,
)


def csv_list(value: str) -> list[str]:
    """Découpe une liste séparée par des virgules en ignorant les éléments vides."""
    return [item.strip() for item in value.split(',') if item.strip()]


print("Configuration pour Anytype chargée avec succès.")
