# app/main.py
from fastapi import FastAPI
from app.routes import products, orders, suppliers, warehouses, inventory, auth_router
from app.db import test_connection
from app import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="Smart Inventory API",
    version="1.0.0",
    description="A secure, cloud-native inventory and order management platform running on Azure."
)

app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
app.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])


@app.on_event("startup")
def startup_event():
    logger.info("🚀 Smart Inventory API starting up...")
    test_connection()
    logger.info("✅ Startup checks complete.")


@app.get("/")
def root():
    return {"message": "Welcome to Smart Inventory API (Secure Mode)!"}


# --- New Azure Health Probe Endpoint ---
@app.get("/health", tags=["System"])
def health():
    """
    Lightweight health check endpoint for Azure.
    This ensures Azure App Service startup probes pass instantly.
    """
    return {"status": "healthy", "app": "Smart Inventory API"}
