import azure.functions as func
import logging
import json
import os
import certifi
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from sqlalchemy import create_engine, text
from azure.storage.blob import BlobServiceClient

# ============================================================
# ✅ Setup Logging Configuration
# ============================================================
logging.basicConfig(level=logging.INFO)

# ============================================================
# ✅ Load Environment Variables from Key Vault via Azure Settings
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")
SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

# ============================================================
# ✅ Initialize MySQL Engine (with SSL for Azure)
# ============================================================
ssl_args = {"ssl": {"ca": certifi.where()}}
engine = create_engine(DATABASE_URL, connect_args=ssl_args, pool_pre_ping=True)
logging.info("🔗 MySQL connection engine initialized successfully.")

# ============================================================
# ✅ Initialize Blob Service Client
# ============================================================
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_name = "invoices"

try:
    blob_service_client.create_container(container_name)
    logging.info(f"✅ Azure Blob container '{container_name}' created successfully.")
except Exception:
    logging.info(f"ℹ️ Container '{container_name}' already exists or accessible.")

# ============================================================
# ✅ Initialize Azure Function App
# ============================================================
app = func.FunctionApp()

# ============================================================
# 🧾 PDF Template Class
# ============================================================
class InvoicePDF(FPDF):
    def header(self):
        self.set_fill_color(44, 62, 80)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 15, "Smart Inventory Solutions Pvt. Ltd.", 0, 1, "C", fill=True)
        self.ln(4)

    def footer(self):
        self.set_y(-25)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Thank you for your business!", 0, 1, "C")
        self.cell(0, 10, "Contact: support@smartinventory.com", 0, 0, "C")


# ============================================================
# 🚀 Azure Function Trigger (Service Bus)
# ============================================================
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="order-confirmation-queue",
    connection="SERVICE_BUS_CONNECTION_STRING"
)
def confirm_order(msg: func.ServiceBusMessage):
    logging.info("🚚 Received order confirmation event from Azure Service Bus.")

    try:
        # ---------------------------------------------
        # Step 1️⃣: Decode and Parse Message
        # ---------------------------------------------
        body = msg.get_body().decode("utf-8")
        event = json.loads(body.replace("'", '"'))
        order_id = event["order_id"]
        logging.info(f"📦 Processing Order ID: {order_id}")

        # ---------------------------------------------
        # Step 2️⃣: Update Order Status
        # ---------------------------------------------
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE orders SET status='confirmed' WHERE order_id=:oid"),
                {"oid": order_id}
            )
        logging.info(f"✅ Order {order_id} status updated to 'confirmed' in database.")

        # ---------------------------------------------
        # Step 3️⃣: Fetch Order & Items
        # ---------------------------------------------
        with engine.begin() as conn:
            order = conn.execute(
                text("SELECT * FROM orders WHERE order_id=:oid"),
                {"oid": order_id}
            ).mappings().first()

            items = conn.execute(
                text("SELECT product_id, quantity, price FROM order_items WHERE order_id=:oid"),
                {"oid": order_id}
            ).mappings().all()

        total_amount = sum([float(i['quantity']) * float(i['price']) for i in items])
        logging.info(f"💰 Total invoice amount calculated: {total_amount:.2f} INR")

        # ---------------------------------------------
        # Step 4️⃣: Create Invoice Record
        # ---------------------------------------------
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO invoice(order_id, created_at) VALUES (:oid, NOW())"),
                {"oid": order_id}
            )
        logging.info(f"🧾 Invoice record inserted for Order {order_id}.")

        # ---------------------------------------------
        # Step 5️⃣: Generate Invoice PDF
        # ---------------------------------------------
        pdf = InvoicePDF()
        pdf.add_page()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Invoice #: INV-{order_id:04}", 0, 1, "R")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "R")
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Invoice Details", 0, 1, "L")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(100, 8, f"Order ID: {order_id}", 0, 1)
        pdf.cell(100, 8, f"Warehouse ID: {order['warehouse_id']}", 0, 1)
        pdf.cell(100, 8, "Customer: Syed Saad", 0, 1)
        pdf.ln(8)

        pdf.set_fill_color(41, 128, 185)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(50, 10, "Product ID", 1, 0, "C", True)
        pdf.cell(40, 10, "Quantity", 1, 0, "C", True)
        pdf.cell(50, 10, "Price", 1, 0, "C", True)
        pdf.cell(50, 10, "Total", 1, 1, "C", True)

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        fill = False
        for item in items:
            pid, qty, price = item["product_id"], item["quantity"], item["price"]
            line_total = float(qty) * float(price)
            pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(50, 10, str(pid), 1, 0, "C", fill)
            pdf.cell(40, 10, str(qty), 1, 0, "C", fill)
            pdf.cell(50, 10, f"{price:.2f}", 1, 0, "C", fill)
            pdf.cell(50, 10, f"{line_total:.2f}", 1, 1, "C", fill)
            fill = not fill

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(140, 10, "Grand Total", 1, 0, "R")
        pdf.cell(50, 10, f"INR {total_amount:.2f}", 1, 1, "C")

        pdf_bytes = pdf.output(dest="S").encode("latin1")
        pdf_stream = BytesIO(pdf_bytes)

        # ---------------------------------------------
        # Step 6️⃣: Upload PDF to Blob Storage
        # ---------------------------------------------
        blob_name = f"invoice_order_{order_id}.pdf"
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(pdf_stream, overwrite=True)
        blob_url = blob_client.url
        logging.info(f"☁️ Invoice uploaded to Blob Storage: {blob_url}")

        # ---------------------------------------------
        # Step 7️⃣: Update Database with Blob URL
        # ---------------------------------------------
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE orders SET invoice_blob=:url WHERE order_id=:oid"),
                {"url": blob_url, "oid": order_id}
            )
        logging.info(f"🔗 Invoice Blob URL updated in database for Order {order_id}")

        # ---------------------------------------------
        # ✅ Success
        # ---------------------------------------------
        logging.info(f"✅ Order {order_id} confirmed, invoice generated, and uploaded successfully.")
        logging.info(f"📎 Invoice URL: {blob_url}")

    except Exception as e:
        logging.error(f"❌ Error in order confirmation function: {str(e)}", exc_info=True)
        raise


# ============================================================
# 🧠 Optional Health Check Route
# ============================================================
@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("✅ Smart Inventory FunctionApp is active and healthy!", status_code=200)
