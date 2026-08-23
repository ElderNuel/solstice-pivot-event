# Solstice Events Kiosk - Asynchronous UI (Assignment 2 Pivot)

**Project:** Power Learn Project - The Meridian Pivot  
**Client:** Solstice Events Co.  
**Component:** Frontend Kiosk (`index.html`)

This repository contains the frontend component of the refactored Solstice Events Co. check-in kiosk.

Following a mid-sprint requirement pivot, the original blocking synchronous badge-printing workflow was redesigned around an **asynchronous message queue architecture**. Instead of making the kiosk wait for an external badge-printer service to complete before responding, the frontend receives an immediate **pending** response and then waits for a real-time WebSocket notification when the asynchronous printing workflow is completed.

The frontend demonstrates how a kiosk can provide a responsive user experience even when the backend depends on delayed processing and an external vendor webhook.

### Core Flow

```text
Kiosk Scan
    ↓
FastAPI REST API
    ↓
RabbitMQ vendor_print_queue
    ↓
External/Simulated Printer
    ↓
Printer Webhook Callback
    ↓
FastAPI
    ↓
WebSocket Broadcast
    ↓
Kiosk UI Updates Automatically
```

---

# 📌 What the Frontend Does

The `index.html` file provides the user interface used by Solstice Events staff to process attendee check-ins.

The frontend is responsible for:

1. Accepting an attendee ID from the kiosk operator.
2. Sending the attendee ID to the FastAPI check-in endpoint.
3. Displaying an immediate response from the backend.
4. Showing a **pending/yellow** state while the badge-printing job is being processed.
5. Maintaining a persistent WebSocket connection with the FastAPI server.
6. Listening for the printer-completion event.
7. Updating the interface to a **success/green** state when the badge has been printed.
8. Displaying an **error/red** state when duplicate or invalid check-ins are rejected.
9. Allowing the operator to monitor the asynchronous process without refreshing the browser.

---

# 🏗️ Architecture Overview

The complete Assignment 2 Pivot consists of three major application components.

## 1. Frontend Kiosk — `index.html`

The frontend is a lightweight HTML/CSS/vanilla JavaScript application.

It:

- Accepts attendee IDs.
- Sends REST API requests.
- Opens a WebSocket connection.
- Receives real-time check-in completion events.
- Updates the kiosk status dynamically.

The frontend does **not** communicate directly with RabbitMQ.

---

## 2. API Gateway — `main.py`

The FastAPI backend acts as the bridge between the kiosk, RabbitMQ, and the printer callback.

It is responsible for:

- Receiving check-in requests.
- Validating attendee status.
- Preventing duplicate scans.
- Changing eligible attendees to `pending`.
- Publishing badge-print requests to RabbitMQ.
- Receiving the printer vendor webhook.
- Updating the attendee status to `checked_in`.
- Broadcasting completion events through WebSockets.

---

## 3. Message Broker — RabbitMQ

RabbitMQ provides the asynchronous messaging layer.

The queue used by this assignment is:

```text
vendor_print_queue
```

The queue stores pending badge-print jobs until they can be processed by the printer service or simulated printer workflow.

---

# 🔄 Synchronous vs. Asynchronous Pivot

The most important change in Assignment 2 is the transition from a blocking workflow to an asynchronous workflow.

## Previous Synchronous Model

In the original design:

```text
Kiosk
  ↓
API
  ↓
Printer Vendor
  ↓
Wait for printer
  ↓
API Response
  ↓
Kiosk
```

The kiosk could remain blocked while the external printer service completed the job.

---

## New Asynchronous Model

The refactored system works differently:

```text
Kiosk
  ↓
API
  ↓
RabbitMQ
  ↓
Immediate "pending" response
  ↓
Kiosk remains responsive
```

Later:

```text
Printer
  ↓
Webhook
  ↓
API
  ↓
WebSocket
  ↓
Kiosk displays success
```

This allows the kiosk to acknowledge that the job has been queued without waiting for the external printer to finish.

---

# 🎨 Frontend Status States

The frontend should communicate the current state of the check-in clearly.

| State | Typical UI | Meaning |
|---|---|---|
| Ready | Neutral/default | Kiosk is ready for an attendee |
| Processing | Blue | Check-in request is being submitted |
| Pending | 🟨 Yellow | Print request has been queued |
| Success | 🟩 Green | Badge printing completed successfully |
| Error | 🟥 Red | Check-in was rejected or an error occurred |

### Pending State

Example:

```text
⏳ Print job queued for ATT-001. Waiting for printer...
```

This means the API accepted the request and the badge-print job is now being handled asynchronously.

### Success State

Example:

```text
✅ ATT-001 Checked In & Badge Printed!
```

This means the printer callback was received and the backend successfully notified the frontend.

### Duplicate/Error State

Example:

```text
❌ Error: Attendee already checked in or pending
```

This prevents an attendee from receiving multiple badge-print jobs.

---

# 📂 Expected Project Structure

A typical project directory should contain:

```text
solstice-kiosk/
│
├── index.html
├── main.py
├── README.md
│
└── [optional project files]
```

### File Responsibilities

| File/Component | Responsibility |
|---|---|
| `index.html` | Kiosk interface, REST requests, WebSocket client |
| `main.py` | FastAPI API, attendee state management, webhook, WebSocket |
| RabbitMQ | Asynchronous badge-print message broker |
| `vendor_print_queue` | Queue containing badge-print jobs |
| `README.md` | Project documentation |

---

# ⚙️ Prerequisites

Before running the application, ensure the following software is installed.

## Required Software

- **Python 3.8+**
- **Docker Desktop**
- **Git Bash, PowerShell, Command Prompt, or another terminal**
- A modern web browser:
  - Google Chrome
  - Microsoft Edge
  - Mozilla Firefox

---

# 📦 Install Python Dependencies

Open a terminal in the project directory and run:

```bash
pip install fastapi "uvicorn[standard]" pika
```

### Why `uvicorn[standard]`?

The frontend communicates with FastAPI through a WebSocket connection.

The standard Uvicorn installation includes the additional WebSocket-related dependencies needed to support the connection properly.

If you already installed the packages, you can verify FastAPI and Uvicorn with:

```bash
pip show fastapi
pip show uvicorn
```

Verify Pika with:

```bash
pip show pika
```

---

# 🚀 Step-by-Step Execution Guide

For the complete end-to-end test, you need:

1. RabbitMQ running.
2. FastAPI running.
3. The frontend kiosk open in a browser.
4. A terminal available to simulate the printer webhook.

Unlike Assignment 1, the provided Assignment 2 flow does **not** require a separate `consumer.py` process if `main.py` is responsible for publishing the queue message and the printer callback is being simulated manually through the webhook endpoint.

---

# Step 1 — Open the Project Directory

Open Git Bash, PowerShell, Command Prompt, or your preferred terminal.

Navigate to the directory containing `main.py` and `index.html`.

Example:

```bash
cd path/to/solstice-kiosk
```

Verify the files.

### Git Bash

```bash
ls
```

### Windows Command Prompt

```cmd
dir
```

You should see something similar to:

```text
index.html
main.py
README.md
```

---

# Step 2 — Start RabbitMQ

RabbitMQ is the message broker used by the asynchronous kiosk backend.

Open **Terminal 1** and run:

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
```

Keep this terminal running.

## RabbitMQ Ports

| Port | Purpose |
|---|---|
| `5672` | AMQP/RabbitMQ application connection |
| `15672` | RabbitMQ Management Dashboard |

---

# Step 3 — Verify RabbitMQ

Open a browser and visit:

```text
http://localhost:15672
```

The RabbitMQ Management Dashboard should load if the management plugin is available.

For a default local RabbitMQ development installation, the commonly used credentials are:

```text
Username: guest
Password: guest
```

The exact credentials depend on your RabbitMQ configuration.

The important requirement is that RabbitMQ is running and accepting connections on:

```text
localhost:5672
```

---

# Step 4 — Start the FastAPI Backend

Open **Terminal 2**.

Navigate to the directory containing `main.py`:

```bash
cd path/to/solstice-kiosk
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

The API should become available at:

```text
http://127.0.0.1:8000
```

Keep this terminal running.

---

# Step 5 — Verify the FastAPI Server

Open:

```text
http://127.0.0.1:8000
```

If your application defines a root route, you should receive its corresponding response.

You can also open the automatically generated FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

The Swagger UI is useful for inspecting the available API endpoints and testing requests independently of the kiosk frontend.

---

# Step 6 — Launch the Frontend Kiosk

Locate:

```text
index.html
```

Double-click the file to open it in Chrome, Edge, Firefox, or another modern browser.

The kiosk interface should load.

The frontend should attempt to establish a WebSocket connection with:

```text
http://127.0.0.1:8000
```

The exact WebSocket URL depends on the implementation in `index.html`.

> **Important:** The browser frontend requires the FastAPI server to be running. Opening `index.html` without starting the backend will not demonstrate the complete application.

---

# 🔌 How the WebSocket Workflow Works

The WebSocket connection is responsible for delivering the final check-in result to the kiosk.

When the kiosk loads:

```text
Browser
   │
   │ WebSocket connection
   ▼
FastAPI
```

The connection remains open.

After the printer webhook is received:

```text
Printer
   │
   │ POST webhook
   ▼
FastAPI
   │
   │ WebSocket broadcast
   ▼
Browser
```

The frontend receives the event and updates the attendee's status without a page refresh.

---

# 🧪 End-to-End Testing

The primary test should simulate the complete asynchronous check-in workflow.

Use:

```text
ATT-001
```

as the first test attendee.

---

# Test 1 — Live WebSocket Transition

## Step 1: Open the Kiosk

Open `index.html` in your browser.

Make sure the kiosk interface is visible.

---

## Step 2: Scan the Attendee

In the attendee ID input field, enter:

```text
ATT-001
```

Click:

```text
Process Check-In
```

---

## Step 3: Observe the Pending State

The frontend should immediately display a **yellow/pending** status similar to:

```text
⏳ Print job queued for ATT-001. Waiting for printer...
```

This is an important part of the Assignment 2 pivot.

The kiosk does **not** wait for the printer to finish.

Instead, it tells the operator that the print job has been queued.

---

## Step 4: Simulate the Printer Callback

Open another terminal.

Use `curl` to simulate the external printer vendor notifying the backend that the badge has been printed successfully:

### Git Bash

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "success"}'
```

If your shell does not support the multiline format above, use:

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback -H "Content-Type: application/json" -d "{\"attendee_id\":\"ATT-001\",\"status\":\"success\"}"
```

The webhook request simulates the external printer service.

---

## Step 5: Observe the Real-Time UI Update

Return your attention to the browser.

Do **not** refresh the page.

The yellow pending status should automatically change to a **green success** status similar to:

```text
✅ ATT-001 Checked In & Badge Printed!
```

This demonstrates that the WebSocket connection is functioning correctly.

---

# 🔬 What Happened During Test 1?

The complete sequence was:

```text
1. Operator enters ATT-001
             ↓
2. Frontend sends REST POST
             ↓
3. FastAPI validates attendee
             ↓
4. Attendee becomes "pending"
             ↓
5. FastAPI publishes print request
             ↓
6. Frontend receives pending response
             ↓
7. UI displays yellow status
             ↓
8. Printer completes badge printing
             ↓
9. Printer sends webhook
             ↓
10. FastAPI receives callback
             ↓
11. Attendee becomes "checked_in"
             ↓
12. FastAPI broadcasts WebSocket event
             ↓
13. Browser receives event
             ↓
14. UI changes to green
```

This is the central demonstration of the Assignment 2 asynchronous pivot.

---

# 🧪 Test 2 — Duplicate Scan Protection

The system must prevent the same attendee from being processed repeatedly.

Once `ATT-001` has successfully completed the previous test, attempt to scan it again.

## Step 1

Enter:

```text
ATT-001
```

## Step 2

Click:

```text
Process Check-In
```

## Expected Result

The frontend should display a **red error** similar to:

```text
❌ Error: Attendee already checked in or pending
```

The backend should reject the duplicate check-in.

No additional badge-print request should be created for the already processed attendee.

---

# 🧪 Test 3 — Pending Duplicate Protection

The backend should also prevent duplicate scans while an attendee is still pending.

To test this behavior:

1. Start with an attendee that has not yet been completed.
2. Submit the attendee ID.
3. Wait for the yellow pending state.
4. Before sending the printer webhook, submit the same attendee ID again.

The second request should be rejected because the attendee is already in the:

```text
pending
```

state.

The expected behavior is similar to:

```text
❌ Error: Attendee already checked in or pending
```

This protects the system from accidentally creating multiple print jobs for the same attendee.

---

# 🧪 Test 4 — Pre-Checked-In Attendee

The mock database may contain an attendee such as:

```text
ATT-002
```

that is already marked as checked in.

Enter:

```text
ATT-002
```

and click:

```text
Process Check-In
```

Expected result:

```text
❌ Error: Attendee already checked in or pending
```

This confirms that duplicate protection works against an attendee whose state is already:

```text
checked_in
```

---

# 🧪 Test 5 — Successful Webhook

The webhook payload used for a successful printer completion is:

```json
{
  "attendee_id": "ATT-001",
  "status": "success"
}
```

Send it to:

```text
http://127.0.0.1:8000/webhook/printer-callback
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "success"}'
```

The expected effect is:

```text
pending
   ↓
checked_in
```

and the frontend should receive the corresponding WebSocket event.

---

# 🧪 Test 6 — Failed Printer Callback

If the backend supports printer failure statuses, you can test a failure payload such as:

```json
{
  "attendee_id": "ATT-001",
  "status": "failed"
}
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "failed"}'
```

The exact frontend behavior depends on the implementation of `main.py` and `index.html`.

If failure handling is implemented, the kiosk should display an appropriate failure/error state rather than falsely reporting successful check-in.

---

# 🧭 Expected Application States

A typical successful workflow should look like this:

## Initial State

```text
Ready for attendee
```

## After Scan

```text
⏳ Print job queued for ATT-001. Waiting for printer...
```

## After Successful Webhook

```text
✅ ATT-001 Checked In & Badge Printed!
```

## After Duplicate Scan

```text
❌ Error: Attendee already checked in or pending
```

---

# 📊 Expected End-to-End Architecture Test

A successful test should demonstrate the following:

```text
                 SOLSTICE KIOSK

                      │
                      │ REST POST
                      ▼
              ┌───────────────┐
              │    FastAPI    │
              │   main.py     │
              └───────┬───────┘
                      │
                      │ Publish
                      ▼
              ┌───────────────┐
              │   RabbitMQ    │
              │vendor_print_  │
              │    queue      │
              └───────────────┘

                      │
                      │
                Printer Service
                      │
                      │ Webhook
                      ▼
              ┌───────────────┐
              │    FastAPI    │
              └───────┬───────┘
                      │
                      │ WebSocket
                      ▼
              ┌───────────────┐
              │ Kiosk Browser │
              │   Live UI     │
              └───────────────┘
```

---

# 🔍 Browser Developer Tools

If you need to inspect the frontend behavior, open the browser developer tools.

### Chrome / Edge

Press:

```text
F12
```

or:

```text
Ctrl + Shift + I
```

### Firefox

Press:

```text
F12
```

Useful tabs include:

- **Console** — JavaScript and WebSocket errors.
- **Network** — REST API requests.
- **Network → WS** — WebSocket connection and messages.
- **Application** — Browser storage and related information.

---

# 🔌 Inspecting the WebSocket Connection

In Chrome or Edge:

1. Open Developer Tools.
2. Select **Network**.
3. Reload `index.html`.
4. Filter by **WS**.
5. Locate the WebSocket connection.
6. Select it.
7. Inspect the **Messages** tab.

When the printer webhook is fired, you should see a WebSocket message arriving from the backend if the implementation is broadcasting the event correctly.

This is useful for demonstrating that the UI is not polling the server.

---

# 🛑 Troubleshooting

## Problem 1 — WebSocket Fails to Connect

### Symptoms

The kiosk loads, but the UI never receives the final green status.

### Possible Causes

- FastAPI is not running.
- Incorrect WebSocket URL.
- `uvicorn[standard]` was not installed.
- The backend is running on a different port.
- The browser opened the frontend before the backend was available.

### Solution

Run:

```bash
pip install fastapi "uvicorn[standard]" pika
```

Restart FastAPI:

```bash
uvicorn main:app --reload
```

Then reload the frontend.

---

# Problem 2 — UI Stays Yellow

### Symptoms

The kiosk displays:

```text
⏳ Print job queued for ATT-001. Waiting for printer...
```

but never changes to green.

### Check the Following

1. Confirm the FastAPI server is running.
2. Confirm the WebSocket connection is open.
3. Confirm the webhook URL is correct.
4. Confirm the attendee ID matches exactly.
5. Confirm the webhook payload contains:
   ```json
   "status": "success"
   ```
6. Check the FastAPI terminal for errors.
7. Inspect the browser's WebSocket messages.

Send the webhook again if necessary:

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "success"}'
```

---

# Problem 3 — `Connection Refused`

If FastAPI or RabbitMQ reports a connection refusal:

### Check RabbitMQ

```bash
docker ps
```

You should see the RabbitMQ container.

If it is not running, restart it:

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
```

### Check FastAPI

Restart:

```bash
uvicorn main:app --reload
```

---

# Problem 4 — RabbitMQ Connection Error

Make sure:

- Docker Desktop is running.
- RabbitMQ is running.
- Port `5672` is available.
- `main.py` is configured to connect to the correct RabbitMQ host and port.
- Pika is installed.

Install Pika again if necessary:

```bash
pip install pika
```

---

# Problem 5 — RabbitMQ Container Name Already Exists

Check existing containers:

```bash
docker ps -a
```

If an old container named `rabbitmq` exists:

```bash
docker rm -f rabbitmq
```

Then restart:

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
```

---

# Problem 6 — Duplicate Error Appears Unexpectedly

If a test attendee is immediately reported as:

```text
already checked in or pending
```

remember that the application may use an in-memory mock database.

A previous test may have changed the attendee's status.

Restart the FastAPI application:

```text
Ctrl + C
```

Then:

```bash
uvicorn main:app --reload
```

This may reset the in-memory mock database, depending on how `main.py` is implemented.

---

# Problem 7 — `curl` Command Fails

Verify the API is available:

```text
http://127.0.0.1:8000
```

Then verify the webhook path:

```text
http://127.0.0.1:8000/webhook/printer-callback
```

If using Git Bash, use:

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "success"}'
```

If using Windows Command Prompt, the quoting syntax may differ.

---

# 🧹 Stopping the Application

When testing is complete:

## Stop FastAPI

In Terminal 2:

```text
Ctrl + C
```

## Stop RabbitMQ

In Terminal 1:

```text
Ctrl + C
```

Because the Docker command uses:

```text
--rm
```

the RabbitMQ container will automatically be removed when it stops.

## Close the Frontend

Simply close the browser tab containing `index.html`.

---

# 🧠 Key Concepts Demonstrated

This assignment demonstrates several important software engineering concepts.

## 1. Asynchronous Processing

The kiosk does not wait for the printer to finish.

Instead:

```text
Request → Queue → Pending
```

and later:

```text
Webhook → Completion → UI Update
```

---

## 2. Message Queues

RabbitMQ separates task submission from task processing:

```text
Producer
   ↓
RabbitMQ
   ↓
Consumer/Printer
```

This reduces direct coupling between the kiosk and the printer service.

---

## 3. Webhooks

The external printer service can notify the backend when processing is complete.

```text
Printer
   ↓
POST /webhook/printer-callback
   ↓
FastAPI
```

---

## 4. WebSockets

The backend can notify the kiosk immediately:

```text
FastAPI
   ↓
WebSocket
   ↓
Browser
```

The browser does not need to poll the backend continuously.

---

## 5. State Management

The attendee transitions through states:

```text
eligible
   ↓
pending
   ↓
checked_in
```

The system also prevents invalid transitions such as:

```text
checked_in
   ↓
checked_in
```

or:

```text
pending
   ↓
pending
```

when those transitions would create duplicate print jobs.

---

# 🎯 Assignment 2 Pivot — Scope Delta

The frontend reflects the major behavior changes introduced by the requirement pivot.

| Previous Behavior | Refactored Behavior |
|---|---|
| Kiosk waits for printer response | Kiosk receives immediate pending response |
| Synchronous printer call | RabbitMQ-based asynchronous job |
| User waits for completion | User receives real-time status updates |
| Final state returned in same request | Final state delivered through webhook + WebSocket |
| Higher coupling to printer service | Printer processing is decoupled |
| Duplicate scans could trigger repeated work | `pending` and `checked_in` states prevent duplicates |

---

# 📋 Quick Start

For an experienced developer, the setup is:

### Terminal 1 — RabbitMQ

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
```

### Terminal 2 — FastAPI

```bash
pip install fastapi "uvicorn[standard]" pika
uvicorn main:app --reload
```

### Browser

Open:

```text
index.html
```

### Test Attendee

```text
ATT-001
```

### Simulate Printer Completion

```bash
curl -X POST http://127.0.0.1:8000/webhook/printer-callback \
  -H "Content-Type: application/json" \
  -d '{"attendee_id": "ATT-001", "status": "success"}'
```

### Expected UI

```text
⏳ Print job queued for ATT-001. Waiting for printer...
```

followed automatically by:

```text
✅ ATT-001 Checked In & Badge Printed!
```

No browser refresh should be required.

---

# 📚 Testing Checklist

Use this checklist when demonstrating the project.

- [ ] Docker Desktop is running.
- [ ] RabbitMQ container is running.
- [ ] Port `5672` is available.
- [ ] Python 3.8+ is installed.
- [ ] `fastapi` is installed.
- [ ] `uvicorn[standard]` is installed.
- [ ] `pika` is installed.
- [ ] `main.py` starts successfully.
- [ ] FastAPI is available at `http://127.0.0.1:8000`.
- [ ] `index.html` opens successfully.
- [ ] WebSocket connection is established.
- [ ] `ATT-001` can be submitted.
- [ ] The UI displays the yellow pending state.
- [ ] The printer webhook can be triggered with `curl`.
- [ ] The UI automatically changes to green.
- [ ] No page refresh is required.
- [ ] A duplicate `ATT-001` scan is rejected.
- [ ] `ATT-002` is rejected if it is pre-configured as checked in.
- [ ] Browser Developer Tools can show the WebSocket activity.

---

# 🔐 Development Notes

This project is an educational prototype developed for the Power Learn Project's **The Meridian Pivot — Assignment 2**.

It demonstrates the architectural concept of moving from synchronous processing to asynchronous message-driven processing.

For production deployment, additional considerations would be required, including:

- Authentication and authorization
- HTTPS/WSS
- Secure webhook verification
- Persistent database storage
- Message acknowledgement and retry policies
- Dead-letter queues
- Structured logging
- Monitoring and alerting
- Input validation
- Rate limiting
- Production CORS configuration
- Secure RabbitMQ credentials
- Printer/vendor authentication
- Error recovery and idempotency

The current prototype should therefore be treated as a demonstration and learning implementation rather than a production-ready kiosk system.

---

# 👨‍💻 Project

**Solstice Events Kiosk — Asynchronous UI**

**Program:** Power Learn Project  
**Project:** The Meridian Pivot  
**Assignment:** Assignment 2 — Solstice Kiosk Pivot  
**Client:** Solstice Events Co.

---

# 📄 License

This project is an educational prototype created for the Power Learn Project and is intended for learning, demonstration, and architectural reconnaissance purposes.
