# Solstice Events Kiosk Service (Asynchronous Refactor)

**Author:** Emmanuel Chijinkem Ukah  
**Project:** The Meridian Pivot - Assignment 2 (Power Learn Project)  
**Client:** Solstice Events Co.

## Overview

This repository contains the refactored check-in kiosk backend for Solstice Events Co. Following a mid-sprint requirement pivot, the system was transitioned from a synchronous REST architecture to an asynchronous message queue and webhook model using **FastAPI** and **RabbitMQ**.

The refactor removes the obsolete synchronous badge-printing call. Instead, the kiosk immediately records a valid scan as `pending`, publishes a print request to RabbitMQ, and waits for the vendor's asynchronous webhook callback before changing the attendee status to `checked_in`.

## Architecture Overview

The service has three main parts:

1. **Scan Endpoint**  
   When a QR code is scanned, the API verifies that the attendee exists and is not already `pending` or `checked_in`. A valid scan changes the attendee status to `pending` and publishes a print request to RabbitMQ. The endpoint then returns immediately without waiting for printing to finish.

2. **RabbitMQ Message Queue**  
   The `vendor_print_queue` stores badge-print requests. This decouples the kiosk API from the badge-printer vendor and allows the print operation to be processed asynchronously.

3. **Webhook Endpoint**  
   The `/webhook/printer-callback` endpoint receives the vendor's asynchronous completion notification. When a successful callback is received, the attendee's status changes from `pending` to `checked_in`.

### State Flow

```text
QR Scan
   |
   v
Validate attendee
   |
   +---- Unknown attendee ------> 404 Not Found
   |
   +---- pending/checked_in ----> 400 Duplicate
   |
   v
Set status = pending
   |
   v
Publish print request
   |
   v
Return pending response
   |
   v
RabbitMQ / Vendor processing
   |
   v
Printer callback webhook
   |
   +---- success -------------> status = checked_in
   |
   +---- invalid callback ----> 400 Bad Request
```

## Project Structure

A minimal project can be organized as follows:

```text
solstice-kiosk/
├── main.py
└── README.md
```

- `main.py` — FastAPI application containing the attendee mock database, RabbitMQ producer, scan endpoint, and printer webhook.
- `README.md` — setup, usage, testing, and troubleshooting documentation.

## Prerequisites

Before running the service, install or have access to:

- **Python 3.8 or later**
- **Docker Desktop** or another local RabbitMQ installation
- **Git Bash, PowerShell, Command Prompt, or another terminal**
- `pip`, normally included with Python

You should also have the refactored Python script saved as `main.py`.

## Step 1: Create or Open the Project Directory

Create a project folder and place the Python script inside it.

```bash
mkdir solstice-pivot-event
cd solstice-kiosk
```

Save the provided FastAPI code as:

```text
main.py
```

Your directory should now look like:

```text
solstice-kiosk/
└── main.py
```

## Step 2: Create a Python Virtual Environment

Using a virtual environment is recommended so the project's dependencies do not interfere with other Python projects.

### Windows

```bash
python -m venv .venv
```

Activate it in Git Bash:

```bash
source .venv/Scripts/activate
```

Or in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When activated, your terminal will normally show `(.venv)` before the command prompt.

## Step 3: Install Python Dependencies

Install the required packages:

```bash
pip install fastapi uvicorn pika
```

The packages serve these purposes:

| Package | Purpose |
|---|---|
| `fastapi` | Provides the HTTP API framework |
| `uvicorn` | Runs the FastAPI application |
| `pika` | Allows Python to communicate with RabbitMQ |

You can verify the installation with:

```bash
pip show fastapi uvicorn pika
```

## Step 4: Start RabbitMQ

The application expects RabbitMQ to be available on the default AMQP port, `5672`.

If Docker Desktop is installed and running, start RabbitMQ with:

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
```

Leave this terminal running.

The command exposes:

- `5672` — RabbitMQ AMQP connection port used by the Python application.
- `15672` — RabbitMQ management dashboard.

The management dashboard can be opened in a browser at:

```text
http://localhost:15672
```

For the standard RabbitMQ Docker image, the default development credentials are commonly:

```text
Username: guest
Password: guest
```

Do not use default credentials in a production deployment.

### Verify the RabbitMQ Container

In another terminal, run:

```bash
docker ps
```

You should see a container named:

```text
rabbitmq
```

## Step 5: Start the FastAPI Server

Open another terminal and navigate to the project directory.

If your virtual environment is not active, activate it first.

Then run:

```bash
uvicorn main:app --reload
```

The application should start on:

```text
http://127.0.0.1:8000
```

You should see output similar to:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The `--reload` option is useful during development because Uvicorn automatically reloads the application when the source file changes.

## Step 6: Open the FastAPI Documentation

FastAPI automatically provides interactive API documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

You can use the Swagger UI to inspect and manually execute:

- `POST /api/scan/{attendee_id}`
- `POST /webhook/printer-callback`

An alternative documentation page is available at:

```text
http://127.0.0.1:8000/redoc
```

## API Behavior

### `POST /api/scan/{attendee_id}`

This endpoint represents a QR-code scan.

For a valid attendee whose status is `unregistered`:

1. The attendee is located in the mock database.
2. The current status is checked.
3. The status is changed to `pending`.
4. A print request is published to RabbitMQ.
5. The API immediately returns a `pending` response.

Example:

```http
POST /api/scan/ATT-001
```

Expected response:

```json
{
  "message": "Print job queued",
  "status": "pending"
}
```

### `POST /webhook/printer-callback`

This endpoint represents the badge-printer vendor notifying the application that a print job has completed.

A successful callback contains:

```json
{
  "attendee_id": "ATT-001",
  "status": "success"
}
```

The service then changes the attendee's status from:

```text
pending
```

to:

```text
checked_in
```

## Test Data

The script contains three mock attendees:

| Attendee ID | Name | Initial Status | Testing Purpose |
|---|---|---|---|
| `ATT-001` | Alice | `unregistered` | Normal asynchronous check-in |
| `ATT-002` | Bob | `checked_in` | Duplicate/fully completed scan |
| `ATT-003` | Charlie | `unregistered` | Additional normal check-in test |

Because the database is held in memory, the test state resets whenever the FastAPI process restarts.

# Testing Guide

Perform the following tests in order.

## Test 1: Standard Check-In

Use `ATT-001`, which starts as `unregistered`.

### cURL

```bash
curl -X POST http://127.0.0.1:8000/api/scan/ATT-001
```

### Expected Response

```json
{
  "message": "Print job queued",
  "status": "pending"
}
```

### What This Proves

This verifies that:

- The attendee exists.
- An unregistered attendee can be scanned.
- The status changes to `pending`.
- A print request is sent to RabbitMQ.
- The API does not wait for a synchronous printer response.

## Test 2: Duplicate Scan While Pending

Immediately scan `ATT-001` again.

```bash
curl -X POST http://127.0.0.1:8000/api/scan/ATT-001
```

### Expected Response

HTTP status:

```text
400 Bad Request
```

Response:

```json
{
  "detail": "Attendee already checked in or pending"
}
```

### What This Proves

The expanded duplicate protection prevents a second scan while the first badge-print request is still being processed.

This is important in the asynchronous architecture because the attendee remains `pending` until the webhook arrives.

## Test 3: Simulate a Successful Printer Callback

Simulate the vendor sending a successful callback for `ATT-001`.

### Git Bash / macOS/Linux

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "success"}'
```

### PowerShell

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/webhook/printer-callback" `
  -ContentType "application/json" `
  -Body '{"attendee_id":"ATT-001","status":"success"}'
```

### Expected Response

```json
{
  "status": "acknowledged"
}
```

The FastAPI terminal should also display a message similar to:

```text
[Webhook] ATT-001 successfully checked in.
```

### What This Proves

This verifies the asynchronous completion step:

```text
pending -> checked_in
```

The API did not need to remain blocked while the printer completed the job.

## Test 4: Verify the Final Duplicate State

`ATT-002` starts with:

```text
checked_in
```

Attempt another scan:

```bash
curl -X POST http://127.0.0.1:8000/api/scan/ATT-002
```

### Expected Response

HTTP status:

```text
400 Bad Request
```

Response:

```json
{
  "detail": "Attendee already checked in or pending"
}
```

### What This Proves

The duplicate protection works for an attendee who has already completed the asynchronous check-in process.

## Test 5: Unknown Attendee

Test an attendee ID that does not exist:

```bash
curl -X POST http://127.0.0.1:8000/api/scan/ATT-999
```

### Expected Response

HTTP status:

```text
404 Not Found
```

Response:

```json
{
  "detail": "Attendee not found"
}
```

### What This Proves

The endpoint correctly rejects unknown attendee IDs instead of creating an invalid check-in request.

## Test 6: Invalid Webhook Callback

Test a webhook containing an unsupported job status:

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "failed"}'
```

### Expected Response

HTTP status:

```text
400 Bad Request
```

Response:

```json
{
  "detail": "Invalid callback"
}
```

This confirms that only the implemented successful callback path changes an attendee to `checked_in`.

# Observing the RabbitMQ Queue

The application declares a durable queue named:

```text
vendor_print_queue
```

After scanning an attendee, you can inspect the RabbitMQ management interface:

```text
http://localhost:15672
```

Look for the queue:

```text
vendor_print_queue
```

The message published by the FastAPI application has this structure:

```json
{
  "attendee_id": "ATT-001",
  "action": "print_badge"
}
```

The message is marked persistent through RabbitMQ message properties.

## Important Testing Note

The supplied script is a **producer**, not a complete vendor-printing worker.

Therefore, simply publishing a message does not automatically cause a real badge to print. A real deployment would need a consumer/vendor integration that reads `vendor_print_queue`, sends the print request to the badge printer, and calls the webhook after the job completes.

For this assignment, the webhook can be simulated manually with cURL as shown above.

# How the Asynchronous Refactor Differs from the Old Design

The deprecated design performed the printer request synchronously:

```text
Scanner
   |
   v
FastAPI
   |
   v
Printer Vendor API
   |
   v
Wait for response
   |
   v
Return "Checked In"
```

The refactored design is:

```text
Scanner
   |
   v
FastAPI
   |
   +--> status = pending
   |
   +--> RabbitMQ --> vendor/worker
   |
   v
Return immediately

Vendor completes print
   |
   v
Webhook
   |
   v
status = checked_in
```

The key architectural change is that the kiosk no longer treats the printer response as part of the synchronous scan request.

# Why the `pending` State Matters

The `pending` state represents a check-in that has been accepted by the kiosk but has not yet received confirmation that the badge-printing process completed successfully.

It prevents the following race condition:

```text
Scan 1 -> printer request starts
Scan 2 -> arrives before Scan 1 finishes
Scan 2 -> accidentally creates another print request
```

With the new state handling:

```text
Scan 1 -> pending
Scan 2 -> rejected
Webhook -> checked_in
```

This makes the state transition explicit and prevents duplicate scans while the asynchronous operation is in progress.

# Troubleshooting

## RabbitMQ Connection Error

If the application reports a connection error involving `localhost:5672`, verify that the RabbitMQ container is running:

```bash
docker ps
```

If it is not running, start it again:

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
```

## `uvicorn` Command Not Found

Make sure the virtual environment is activated and install Uvicorn:

```bash
pip install uvicorn
```

You can also start it through Python:

```bash
python -m uvicorn main:app --reload
```

## `ModuleNotFoundError: pika`

Install the RabbitMQ Python client:

```bash
pip install pika
```

## Port 8000 Already in Use

Start FastAPI on another port:

```bash
uvicorn main:app --reload --port 8001
```

Then use:

```text
http://127.0.0.1:8001
```

for subsequent tests.

## Port 5672 Already in Use

Check whether another RabbitMQ instance or service is already using port `5672`.

If RabbitMQ is already running locally, you do not need to start another Docker container.

# Limitations of the Demonstration

This implementation intentionally uses a simple in-memory dictionary as its database:

```python
attendees = {
    "ATT-001": {"name": "Alice", "status": "unregistered"},
    "ATT-002": {"name": "Bob", "status": "checked_in"},
    "ATT-003": {"name": "Charlie", "status": "unregistered"}
}
```

As a result:

- Data is lost when the application restarts.
- It is not suitable for multiple API workers.
- There is no persistent transaction mechanism.
- There is no production authentication on the webhook.
- Webhook signatures are not verified.
- There is no retry/dead-letter strategy for failed messages.
- There is no real badge-printer vendor consumer in this demonstration.
- The RabbitMQ connection is created for each publish operation.

These are acceptable limitations for a small assignment demonstration but should be addressed before production deployment.

# Recommended Production Improvements

For a production-ready version, the following improvements should be considered:

1. Replace the in-memory dictionary with a persistent database such as PostgreSQL.
2. Add database transactions or atomic state transitions to strengthen duplicate-scan protection.
3. Reuse or pool RabbitMQ connections rather than creating a new connection for every request.
4. Add a dedicated RabbitMQ consumer/worker for vendor printing.
5. Add message retry and dead-letter queues.
6. Authenticate and authorize the printer webhook.
7. Verify webhook signatures to prevent forged callbacks.
8. Add idempotency handling for repeated vendor callbacks.
9. Add structured logging and monitoring.
10. Add automated unit and integration tests.
11. Add WebSocket or long-polling support so the kiosk UI can observe `pending -> checked_in` without manually refreshing.
12. Add proper environment-variable configuration for RabbitMQ and vendor credentials.

# End-to-End Test Summary

A successful test should follow this sequence:

```text
1. Start RabbitMQ
       |
       v
2. Start FastAPI
       |
       v
3. Scan ATT-001
       |
       v
4. API returns pending
       |
       v
5. Print request enters vendor_print_queue
       |
       v
6. Simulate successful webhook
       |
       v
7. ATT-001 becomes checked_in
       |
       v
8. Scan ATT-001 again
       |
       v
9. API rejects duplicate scan with HTTP 400
```

## Expected Assignment Outcome

The refactored service demonstrates the required mid-sprint architectural pivot:

- The obsolete synchronous printer API call has been removed.
- The scan endpoint returns immediately with a `pending` status.
- Print requests are published asynchronously through RabbitMQ.
- Duplicate scans are rejected for both `pending` and `checked_in` attendees.
- A webhook completes the asynchronous state transition to `checked_in`.
- The API can be run and tested locally using FastAPI, RabbitMQ, Docker, and cURL.
