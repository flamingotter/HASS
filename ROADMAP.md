# Development Roadmap

This document tracks active projects, pending infrastructure fixes, and long-term goals for the Home Assistant deployment.

---

## 1. Immediate Infrastructure & Hardware Fixes
- [x] **Bluetooth Stability:** Host-level settings updated May 6, 2026. Monitoring for stability.
- [ ] **Porch Cameras:** Finalize constant frame rate (CFR) settings on porch cameras to resolve `Errno 22` video recording errors.
- [x] **BigQuery Integration:** Re-created `bq_venv`, verified `hvac_health_check.py` functionality, and hardened credentials path. (Completed May 6, 2026)
- [ ] **Hardware Maintenance:** 
    - Re-add `light.masonic_lamp` to the network.
    - Physical install and entity update for `binary_sensor.bedroom_door` (replaces `binary_sensor.bedroom`).

## 2. Climate & Energy (The Sleep Engine v7.x)
- [ ] **v7.2 Pilot Phase:** Monitor the new Fail-Safe logic and Data Armor swing caps over the next 7 days.
- [ ] **Repository Re-baselining:** Monitor the 80°F bin (manually set to 50.0) to ensure the AI Auditor validates new, faster cooling rates.
- [ ] **Decommissioning:** Once v7.2 is proven stable, disable the legacy v6.3 automation in the UI to prevent logic overlaps.

## 3. Presence & Global Logic
- [ ] **Eco Mode Validation:** Verify the first real-world 500-mile "Extended Away" trigger.
- [ ] **Proximity Testing:** Confirm both Josh and MJ entering the 50-mile radius correctly releases Eco Mode.

## 4. Maintenance & Housekeeping
- [ ] **Automations Audit - Bit Rot:** 
    - **Entertainment Automations:** Reference `light.masonic_lamp` and `light.parlor_light`. Currently **Disabled/In Stasis**.
    - **Nightly Climate Data:** Reference `button.docker_ha_bq_exporter_restart` is valid (entity only appears when container runs).
- [ ] **Script Modernization:** Ensure all scripts in `scripts.yaml` use the `action:` syntax for consistency with HA 2026.4.

## 5. Future AI Enhancements
- [ ] **Vision AI Expansion:** Explore using the parlor/kitchen vision pattern for more complex occupancy sensing (e.g., distinguishing between owners and guests).
- [ ] **Natural Language Control:** Expand the `ai_task` timer parser to handle more complex scheduling requests via actionable notifications.
