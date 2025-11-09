# app/config.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("config")

# Azure Key Vault URL (your vault name)
KEY_VAULT_URL = "https://smartvault-saad2.vault.azure.net/"

# Create credential using Managed Identity (App Service identity)
try:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    logger.info("✅ Connected to Azure Key Vault successfully")
except Exception as e:
    logger.error(f"❌ Failed to connect to Key Vault: {e}")
    raise e

# Fetch secrets from Azure Key Vault
def get_secret(secret_name: str) -> str:
    """Retrieve a secret safely from Azure Key Vault"""
    try:
        secret = client.get_secret(secret_name)
        logger.info(f"✅ Retrieved secret: {secret_name}")
        return secret.value
    except Exception as e:
        logger.error(f"❌ Failed to retrieve secret {secret_name}: {e}")
        return None

# --- Load all required secrets ---
DB_URL = get_secret("mysql-connection-string")
STORAGE_CONNECTION = get_secret("azure-storage-connection-string")
SERVICE_BUS_CONNECTION = get_secret("service-bus-connection-string")

# Optional: Export as environment variables for other modules
os.environ["DATABASE_URL"] = DB_URL or ""
os.environ["STORAGE_CONNECTION_STRING"] = STORAGE_CONNECTION or ""
os.environ["SERVICE_BUS_CONNECTION_STRING"] = SERVICE_BUS_CONNECTION or ""

logger.info("✅ All secrets loaded and environment variables set.")
