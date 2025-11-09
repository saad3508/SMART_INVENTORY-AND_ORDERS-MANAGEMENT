# app/database.py
import os
import logging
from sqlalchemy import create_engine, text
from app import config  # Ensure Key Vault secrets are loaded first

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# Load the DATABASE_URL (from Key Vault via config.py)
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    logger.error("❌ DATABASE_URL is missing. Ensure Key Vault secrets are loaded correctly.")
else:
    logger.info("✅ DATABASE_URL successfully loaded from Key Vault or environment.")

# Create SQLAlchemy engine
try:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    logger.info("✅ SQLAlchemy engine created successfully.")
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}")
    engine = None


def test_connection():
    """Test MySQL database connection"""
    if not engine:
        logger.error("⚠️ Database engine not initialized.")
        return
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"✅ Database connection successful: {result.fetchone()}")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")


if __name__ == "__main__":
    test_connection()
