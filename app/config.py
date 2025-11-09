# app/config.py
import os
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("config")

# --- Azure Key Vault Configuration ---
KEY_VAULT_NAME = "smartvault-saad2"
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net/"

# Initialize Azure credentials
# - Locally uses Azure CLI login
# - On Azure App Service uses Managed Identity
try:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KV_URI, credential=credential)
    logger.info("✅ Connected to Azure Key Vault successfully.")
except Exception as e:
    logger.error(f"❌ Failed to connect to Key Vault: {e}")
    client = None


def get_secret(secret_name: str):
    """
    Fetch secret from Azure Key Vault.
    Fallback to environment variable if Key Vault is not reachable.
    """
    try:
        if client:
            secret = client.get_secret(secret_name)
            logger.info(f"🔐 Loaded secret from Key Vault: {secret_name}")
            return secret.value
        else:
            raise Exception("Key Vault client not initialized.")
    except Exception as e:
        logger.warning(f"⚠️ Could not load '{secret_name}' from Key Vault. Using environment fallback. Error: {e}")
        return os.getenv(secret_name)


# --- Securely Fetch All Required Secrets ---
DB_HOST = get_secret("db-host")
DB_NAME = get_secret("db-name")
DB_USER = get_secret("db-user")
DB_PASSWORD = get_secret("db-password")
SERVICE_BUS_CONNECTION = get_secret("service-bus-connection")
STORAGE_CONNECTION_STRING = get_secret("storage-connection-string")

# --- Construct SQLAlchemy DB URL ---
if DB_HOST and DB_NAME and DB_USER and DB_PASSWORD:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    os.environ["DATABASE_URL"] = DATABASE_URL  # Make accessible globally
    logger.info("✅ DATABASE_URL constructed successfully from Key Vault secrets.")
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    logger.warning("⚠️ Some DB secrets missing. Using fallback DATABASE_URL.")
