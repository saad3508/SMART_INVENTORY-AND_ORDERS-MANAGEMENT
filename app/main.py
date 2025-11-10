# app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import logging

from app.routes import products, orders, suppliers, warehouses, inventory, auth_router
from app.db import test_connection, engine, get_db
from app import models

# ------------------ Logging Configuration ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# ------------------ FastAPI Initialization ------------------
app = FastAPI(
    title="Smart Inventory API",
    version="1.0.0",
    description="A secure, cloud-native inventory and order management platform running on Azure."
)

# ------------------ Database Setup ------------------
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully.")
except Exception as e:
    logger.error(f"❌ Failed to initialize database tables: {e}")

# ------------------ Startup Event ------------------
@app.on_event("startup")
def startup_event():
    """Executed when the app starts (useful for logging & DB check)."""
    logger.info("🚀 Smart Inventory API starting up...")
    try:
        test_connection()
        logger.info("✅ Startup checks complete.")
    except Exception as e:
        logger.warning(f"⚠️ Startup DB connection check failed: {e}")

# ------------------ Root Routes ------------------
@app.get("/", tags=["System"])
def root():
    """Welcome message."""
    return {"message": "Welcome to Smart Inventory API (Azure-Ready Mode)!"}

@app.get("/health", tags=["System"])
def health():
    """Simple endpoint for Azure health probe."""
    return {"status": "healthy", "app": "Smart Inventory API"}

@app.get("/test-db", tags=["System"])
def test_db(db: Session = Depends(get_db)):
    """Database connection test."""
    try:
        result = db.execute("SELECT NOW()").fetchone()
        return {"message": "✅ Database Connected", "time": str(result[0])}
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return {"error": str(e)}

# ------------------ Include Routers ------------------
try:
    app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
    app.include_router(products.router, prefix="/products", tags=["Products"])
    app.include_router(orders.router, prefix="/orders", tags=["Orders"])
    app.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
    app.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
    app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
    logger.info("✅ Routers registered successfully.")
except Exception as e:
    logger.warning(f"⚠️ Some routers failed to load: {e}")

# ------------------ Local Debug Entry Point ------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
