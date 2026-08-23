from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import pika
import json
from typing import List

app = FastAPI()

# 1. Enable CORS for the frontend HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# In-memory mock database
attendees = {
    "ATT-001": {"name": "Alice", "status": "unregistered"},
    "ATT-002": {"name": "Bob", "status": "checked_in"}, # Duplicate test case
    "ATT-003": {"name": "Charlie", "status": "unregistered"}
}

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
    if attendee_id not in attendees:
        raise HTTPException(status_code=404, detail="Attendee not found")
        
    current_status = attendees[attendee_id]["status"]
    
    if current_status in ["checked_in", "pending"]:
        raise HTTPException(status_code=400, detail="Attendee already checked in or pending")

    attendees[attendee_id]["status"] = "pending"
    publish_print_request(attendee_id)
    
    return {"message": "Print job queued", "status": "pending"}

@app.post("/webhook/printer-callback")
async def printer_webhook(request: Request):
    """Webhook receives async callback from vendor and broadcasts to UI."""
    payload = await request.json()
    attendee_id = payload.get("attendee_id")
    job_status = payload.get("status")

    if job_status == "success" and attendee_id in attendees:
        attendees[attendee_id]["status"] = "checked_in"
        print(f"[Webhook] {attendee_id} successfully checked in.")
        
        # 3. Broadcast the success to the frontend kiosk!
        await manager.broadcast({"attendee_id": attendee_id, "status": "success"})
        
        return {"status": "acknowledged"}
    
    raise HTTPException(status_code=400, detail="Invalid callback")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)