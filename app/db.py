# app/db.py
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app import config  # Ensure Key Vault secrets load first

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# --- Load DB URL from environment (after Key Vault loads) ---
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    logger.error("❌ DATABASE_URL missing — check Key Vault configuration.")
else:
    logger.info("✅ DATABASE_URL successfully loaded from Key Vault or environment.")

# --- SQLAlchemy setup ---
try:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()  # ✅ Define Base for models.py
    logger.info("✅ SQLAlchemy engine created successfully.")
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}")
    engine = None
    SessionLocal = None
    Base = None


# --- DB Dependency for FastAPI Routes ---
def get_db():
    """Provide a SQLAlchemy DB session per request."""
    if not SessionLocal:
        raise Exception("❌ Database session not initialized — check DB_URL or Key Vault secrets.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- DB Connection Test ---
def test_connection():
    """Simple check to confirm MySQL connection works."""
    if not engine:
        logger.error("⚠️ Database engine not initialized.")
        return
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"✅ Database connection successful: {result.fetchone()}")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")


# Run test manually if executed directly
if __name__ == "__main__":
    test_connection()
