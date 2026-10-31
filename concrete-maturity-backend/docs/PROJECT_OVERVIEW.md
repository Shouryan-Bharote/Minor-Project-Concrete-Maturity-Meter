# Project Overview: ESP32 Concrete Maturity Meter & FastAPI Integration

## Mission
The Concrete Maturity Meter is an IoT-enabled telemetry and analytics system designed to track concrete curing in real-time. By applying the **Nurse-Saul maturity equation**, engineers and site managers can reliably forecast compressive strength and determine exactly when it is safe to remove formwork, speeding up construction cycles while guaranteeing structural integrity.

## Core Features
1. **Nurse-Saul Maturity Tracking**: Automatic integration of time and temperature history against standard datum temperatures (default $-10^\circ\text{C}$).
2. **Robust IoT Integration**: Designed for ESP32-S3 hardware transmitting MQTT to ThingsBoard, forwarded via webhooks to FastAPI.
3. **Real-time Anomaly Detection**: Automatic alerts for freeze hazards, overheating, and hardware disconnection.
4. **Rich Analytics & Dashboards**: Summary KPIs, live sensor telemetry, time-series chart endpoints, and CSV export.
5. **Simulation & Demo Support**: Compatible with firmware simulation modes (`DEMO_MODE` and `USE_DUMMY_DATA`) for bench testing without physical concrete pours.
