# Phase 4: Frontend Web Dashboard

## Objectives
- Build an interactive, real-time web dashboard for site engineers.
- Display summary KPIs (active sensors, active critical alerts, total readings).
- Show live telemetry cards per sensor with Nurse-Saul maturity progress gauge/bar.
- Provide time-series charts for Temperature vs. Time and Cumulative Maturity vs. Time.
- Enable CSV historical data export directly from the UI.

## Acceptance Criteria
- [ ] Dashboard queries `/api/v1/dashboard/summary` and `/api/v1/dashboard/latest`.
- [ ] History charts render dynamically based on date range selection.
- [ ] Responsive design suitable for site tablets and desktops.
