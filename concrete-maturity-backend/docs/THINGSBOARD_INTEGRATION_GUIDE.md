# ThingsBoard Cloud to FastAPI Webhook Integration Guide

This guide walks through connecting the ESP32 (token: `concrete`) via ThingsBoard Cloud to the local FastAPI backend during development and production.

---

## Architecture Flow

```
[ESP32-S3] 
   │  MQTT (port 1883)
   │  Topic: v1/devices/me/telemetry
   │  Token: "concrete"
   ▼
[ThingsBoard Cloud: mqtt.thingsboard.cloud]
   │
   │  Rule Chain: Root Rule Chain
   │  Rule Node: REST API Call
   │  Method: POST
   │  URL: https://<public-tunnel>/api/v1/telemetry
   │  Header: X-API-Key: change-me-super-secret-key
   ▼
[FastAPI Ingestion Endpoint]
   │
   │  Saves to SQLite (`sensor_readings`)
   │  Evaluates thermal alarms
   ▼
[Frontend Dashboard / Client APIs]
```

---

## Step 1: Start the Backend & Public Tunnel

### 1.1 Start FastAPI
In your terminal:
```powershell
cd "d:\Programming\Python\Minor Project\concrete-maturity-backend"
uv run uvicorn app.main:app --reload --port 8000
```

### 1.2 Start an HTTPS Tunnel
ThingsBoard Cloud runs on the public internet and needs a public HTTPS URL to deliver webhooks.

You can use either **Cloudflare Tunnel** or **LocalTunnel** (both free, no sign-up required):

#### Option A: LocalTunnel (via npx, ready immediately)
Open a second terminal window:
```powershell
npx -y localtunnel --port 8000
```
It will output:
```
your url is: https://bright-pandas-sing.loca.lt
```
Your webhook target URL will be:
`https://bright-pandas-sing.loca.lt/api/v1/telemetry`

#### Option B: Cloudflare Tunnel (via winget)
```powershell
winget install Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000
```
It gives you a URL like:
`https://random-subdomain.trycloudflare.com/api/v1/telemetry`

---

## Step 2: ThingsBoard Cloud Rule Chain Setup

1. **Log in to ThingsBoard Cloud**: [https://thingsboard.cloud](https://thingsboard.cloud)
2. **Verify Device**:
   - Go to **Device Groups** -> **All** -> Click on your device (Access Token: `concrete`).
   - Check the **Latest telemetry** tab to ensure readings from `espcode.c` are arriving.
3. **Open the Rule Chain**:
   - In the left sidebar, navigate to **Rule Chains**.
   - Open **Root Rule Chain**.
4. **Add a Filter Node (Optional, Recommended)**:
   - Search for **"message type switch"** or **"filter - script"** in the node palette.
   - If using **Script Filter**, add:
     ```javascript
     return msgType === 'POST_TELEMETRY_REQUEST';
     ```
   - Connect from the input node via the `Post telemetry` relation.
5. **Add the REST API Call Node**:
   - Drag **External** -> **REST API Call** onto the canvas.
   - Name: `Forward to FastAPI Backend`.
   - **Endpoint URL**: `https://<your-tunnel-url>/api/v1/telemetry`
   - **Request Method**: `POST`
   - **Headers**:
     - `Content-Type`: `application/json`
     - `X-API-Key`: `change-me-super-secret-key` *(or your custom key from `.env`)*
   - Leave body empty (it will automatically forward the telemetry JSON payload).
   - Click **Add** and save the Rule Chain.

---

## Step 3: Test Webhook Directly

You can test without waiting for the ESP32 using the included simulation script:

```powershell
cd "d:\Programming\Python\Minor Project\concrete-maturity-backend"
uv run python scripts/simulate_thingsboard_webhook.py --url http://localhost:8000/api/v1/telemetry
```

Or test against your public tunnel URL:
```powershell
uv run python scripts/simulate_thingsboard_webhook.py --url https://<your-tunnel-url>/api/v1/telemetry
```

Expected output:
```
[1/5] ✅ Ingested: reading_id=1, temp=28.5°C, maturity=4.81°C·h
[2/5] ✅ Ingested: reading_id=2, temp=29.0°C, maturity=13.03°C·h
...
```

---

## Step 4: Verify in FastAPI Database & Dashboard

Once data has been received:
- Visit **[http://localhost:8000/docs](http://localhost:8000/docs)**
- Call `GET /api/v1/dashboard/latest` -> see current temperature & Nurse-Saul progress percentage.
- Call `GET /api/v1/dashboard/history?sensor_id=1` -> verify time-series points.
- Call `GET /api/v1/readings` -> see paginated log.
