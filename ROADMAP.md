# Development Roadmap

This document tracks active projects, pending infrastructure fixes, and long-term goals for the Home Assistant deployment.

---

## 1. Immediate Infrastructure Fixes
- [ ] **Bluetooth Stability:** Add `cap_add: [NET_ADMIN, NET_RAW]` to the Docker Compose configuration on the Debian host to resolve `habluetooth.manager` capability errors.
- [ ] **Log Noise Reduction:** Monitor `ambient_station` for KeyError exceptions (batt2, temp2f). If persistent, disable diagnostic entities for Garage Sensor #2.
- [ ] **Camera Hardware Sync:** Finalize constant frame rate (CFR) settings on porch cameras to resolve `Errno 22` video recording errors.

## 2. Climate & Energy (The Sleep Engine v7.x)
- [ ] **v7.2 Pilot Phase:** Monitor the new Fail-Safe logic and Data Armor swing caps over the next 7 days.
- [ ] **Repository Re-baselining:** Continue monitoring the 80°F bin (manually set to 50.0) to ensure the AI Auditor validates new, faster cooling rates.
- [ ] **Decommissioning:** Once v7.2 is proven stable, disable the legacy v6.3 automation in the UI to prevent logic overlaps.

## 3. Presence & Global Logic
- [ ] **Eco Mode Validation:** Verify the first real-world 500-mile "Extended Away" trigger.
- [ ] **Proximity Testing:** Confirm both Josh and MJ entering the 50-mile radius correctly releases Eco Mode.

## 4. Maintenance & Housekeeping
- [ ] **Automations Audit:** Systematically review `automations.yaml` for "bit rot" (entities that moved or no longer exist).
- [ ] **BigQuery Integration:** Ensure the daily `hvac_health_check.py` continues to run successfully in the new `bq_venv` environment.

## 5. Future AI Enhancements
- [ ] **Vision AI Expansion:** Explore using the parlor/kitchen vision pattern for more complex occupancy sensing (e.g., distinguishing between owners and guests).
- [ ] **Natural Language Control:** Expand the `ai_task` timer parser to handle more complex scheduling requests via actionable notifications.
