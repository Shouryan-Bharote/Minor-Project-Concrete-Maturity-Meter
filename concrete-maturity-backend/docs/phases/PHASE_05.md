# Phase 5: Hardware Calibration & Production

## Objectives
- Transition firmware from simulated mode (`USE_DUMMY_DATA false`, `DEMO_MODE false`) to live physical DS18B20 probe readings.
- Calibrate concrete maturity curve against physical cylinder break tests (ASTM C1074).
- Production hardening: evaluate PostgreSQL migration and TLS MQTT (port 8883) on the ESP32-S3.

## Acceptance Criteria
- [ ] Physical DS18B20 transmits actual curing temperatures.
- [ ] OLED display accurately reflects local reading and maturity.
- [ ] Maturity index correlates with lab cylinder break test strengths.
