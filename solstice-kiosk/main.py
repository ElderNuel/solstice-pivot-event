from fastapi import FastAPI, HTTPException, Request
import pika
import json

app = FastAPI()

# In-memory mock database for 3 test attendees
attendees = {
    "ATT-001": {"name": "Alice", "status": "unregistered"},
    "ATT-002": {"name": "Bob", "status": "checked_in"}, # Duplicate test case
    "ATT-003": {"name": "Charlie", "status": "unregistered"}
}

# ==========================================
# OBSOLETE CODE (DEPRECATED AS PER PIVOT)
# ==========================================
# def sync_print_badge(attendee_id):
#     response = requests.post("https://vendor.api/print", data={"id": attendee_id})
#     return response.status_code == 200

# ==========================================
# REFACTORED ASYNC PRODUCER & WEBHOOK
# ==========================================

def publish_print_request(attendee_id):
    """Pushes the print request to the vendor's message queue."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='vendor_print_queue', durable=True)
    
    message = {"attendee_id": attendee_id, "action": "print_badge"}
    channel.basic_publish(
        exchange='',
        routing_key='vendor_print_queue',
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
    )
    connection.close()

@app.post("/api/scan/{attendee_id}")
async def scan_attendee(attendee_id: str):
    """Endpoint triggered when staff scan a QR code."""
    if attendee_id not in attendees:
        raise HTTPException(status_code=404, detail="Attendee not found")
        
    current_status = attendees[attendee_id]["status"]
    
    # Duplicate scan protection holding under the new model
    if current_status in ["checked_in", "pending"]:
        raise HTTPException(status_code=400, detail="Attendee already checked in or pending")

    # Update state to pending and publish to queue
    attendees[attendee_id]["status"] = "pending"
    publish_print_request(attendee_id)
    
    return {"message": "Print job queued", "status": "pending"}

@app.post("/webhook/printer-callback")
async def printer_webhook(request: Request):
    """Webhook endpoint to receive the async callback from the vendor."""
    payload = await request.json()
    attendee_id = payload.get("attendee_id")
    job_status = payload.get("status")

    if job_status == "success" and attendee_id in attendees:
        attendees[attendee_id]["status"] = "checked_in"
        print(f"[Webhook] {attendee_id} successfully checked in.")
        return {"status": "acknowledged"}
    
    raise HTTPException(status_code=400, detail="Invalid callback")