# app/db.py
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv  # ✅ Added for .env support

# --- Load environment variables ---
load_dotenv()

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# --- Load DB URL from environment ---
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    logger.warning("⚠️ DATABASE_URL missing — using fallback configuration for local testing.")
else:
    logger.info("✅ DATABASE_URL loaded successfully.")

# --- SQLAlchemy setup ---
try:
    if DB_URL:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()
        logger.info("✅ SQLAlchemy engine created successfully.")
    else:
        engine = None
        SessionLocal = None
        Base = declarative_base()  # ✅ Dummy Base so models can import
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}")
    engine = None
    SessionLocal = None
    Base = declarative_base()

# --- DB Dependency for FastAPI Routes ---
def get_db():
    """Provide a SQLAlchemy DB session per request."""
    if not SessionLocal:
        raise Exception("❌ Database session not initialized — check DATABASE_URL.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DB Connection Test ---
def test_connection():
    """Simple check to confirm MySQL connection works."""
    if not engine:
        logger.warning("⚠️ Database engine not initialized.")
        return
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"✅ Database connection successful: {result.fetchone()}")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()
