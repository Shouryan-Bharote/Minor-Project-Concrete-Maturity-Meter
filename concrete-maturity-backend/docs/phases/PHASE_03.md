# Phase 3: Dashboard APIs & Business Logic

## Objectives
- Implement MixProfile endpoints to allow custom datum temperatures and target maturity values per pour zone.
- Implement background health heartbeats to flag `DEVICE_DISCONNECTED` when no telemetry arrives for >5 minutes.
- Add alert notification hooks and query filters.

## Acceptance Criteria
- [ ] Users can create and assign mix profiles (e.g. C30/37).
- [ ] Ingestion recalculates progress relative to selected mix target.
- [ ] Alerts trigger and persist on threshold limits and hardware silence.
