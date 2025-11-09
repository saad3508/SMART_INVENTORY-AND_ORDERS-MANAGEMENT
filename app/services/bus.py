import os
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from dotenv import load_dotenv

load_dotenv()

CONN_STR = os.getenv("SERVICE_BUS_CONNECTION_STRING")
QUEUE_NAME = os.getenv("SERVICE_BUS_QUEUE_NAME")

def publish_order_event(order_event: dict):
    with ServiceBusClient.from_connection_string(CONN_STR) as client:
        sender = client.get_queue_sender(QUEUE_NAME)
        with sender:
            message = ServiceBusMessage(str(order_event))
            sender.send_messages(message)
