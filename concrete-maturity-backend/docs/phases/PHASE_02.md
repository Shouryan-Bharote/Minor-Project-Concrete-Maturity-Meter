# Phase 2: Ingestion & Cloud Forwarding

## Objectives
- Integrate with ThingsBoard Cloud IoT platform.
- Configure Rule Engine with a `REST API Call Node` forwarding telemetry to the FastAPI backend.
- Set up a secure reverse tunnel (e.g. ngrok or Cloudflare Tunnel) during local development.
- Secure the webhook endpoint with the `X-API-Key` secret header.

## Ingestion Contract
```json
{
  "sensor_id": 1,
  "temperature_c": 28.50,
  "maturity_c_hour": 6.417,
  "simulated_hours": 0.167,
  "sensor_status": true,
  "data_mode": "dummy"
}
```

## Acceptance Criteria
- [ ] ThingsBoard successfully dispatches HTTP POST payloads to `https://<public-url>/api/v1/telemetry`.
- [ ] Telemetry entries persist correctly in `sensor_readings`.
- [ ] Unauthorized requests without `X-API-Key` receive HTTP 403 Forbidden.
