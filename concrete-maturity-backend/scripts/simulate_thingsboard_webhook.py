"""
Simulate ThingsBoard Cloud forwarding telemetry to the FastAPI backend.

Usage:
    uv run python scripts/simulate_thingsboard_webhook.py [--url URL] [--key KEY]
"""

import argparse
import sys
import time

try:
    import httpx
except ImportError:
    print("httpx is required. Run: uv sync")
    sys.exit(1)


def simulate(url: str, api_key: str, count: int = 5, delay: float = 2.0):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }

    print(f"📡 Forwarding simulated ThingsBoard telemetry to: {url}")
    print(f"🔑 Using X-API-Key: {api_key}")
    print(f"📊 Sending {count} readings with {delay}s interval...\n")

    for i in range(1, count + 1):
        temp = 28.0 + (i % 8) * 0.5
        sim_hours = i * 0.167
        maturity = (temp - (-10.0)) * sim_hours

        payload = {
            "sensor_id": 1,
            "temperature_c": round(temp, 2),
            "maturity_c_hour": round(maturity, 3),
            "simulated_hours": round(sim_hours, 3),
            "sensor_status": True,
            "data_mode": "dummy",
            "ts": int(time.time() * 1000),
        }

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=5.0)
            if response.status_code == 201:
                data = response.json()
                print(
                    f"[{i}/{count}] ✅ Ingested: reading_id={data.get('reading_id')}, "
                    f"temp={temp}°C, maturity={round(maturity, 2)}°C·h"
                )
            else:
                print(f"[{i}/{count}] ❌ HTTP {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[{i}/{count}] ❌ Request failed: {e}")

        if i < count:
            time.sleep(delay)

    print("\n🏁 Simulation completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate ThingsBoard webhook telemetry.")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/v1/telemetry",
        help="Target FastAPI telemetry endpoint",
    )
    parser.add_argument(
        "--key",
        default="change-me-super-secret-key",
        help="Webhook API Key (matches WEBHOOK_API_KEY in .env)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of telemetry messages to send",
    )
    args = parser.parse_args()

    simulate(url=args.url, api_key=args.key, count=args.count)
