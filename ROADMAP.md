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
- [x] **v7.2 Pilot Phase:** Monitor the new Fail-Safe logic and Data Armor swing caps. (Deployed May 6, 2026)
- [x] **Repository Re-baselining:** Bin 80 re-baselined to 50.0 to prevent early starts.
- [ ] **Decommissioning:** Once v7.2 is proven stable, disable the legacy v6.3 automation in the UI to prevent logic overlaps.

## 3. Presence & Global Logic
- [ ] **Eco Mode Validation:** Verify the first real-world 500-mile "Extended Away" trigger.
- [ ] **Proximity Testing:** Confirm both Josh and MJ entering the 50-mile radius correctly releases Eco Mode.

## 4. Maintenance & Housekeeping
- [ ] **Automations Audit - Bit Rot:** 
    - **Entertainment Automations:** Reference `light.masonic_lamp` and `light.parlor_light`. Currently **Disabled/In Stasis**.
    - **Nightly Climate Data:** Reference `button.docker_ha_bq_exporter_restart` is valid (entity only appears when container runs).
- [x] **Script Modernization:** All scripts in `scripts.yaml` updated to `action:` syntax and AI attributes corrected from `.text` to `.data`. (Completed May 6, 2026)
- [x] **NFC Unification:** Implemented `System: NFC Tag Manager` as a centralized switchboard for physical tags. (Completed May 7, 2026)
- [x] **Labeling Strategy:** Established AI-specific labeling scheme (`ai_engine`, `ai_vision`, `ai_persona`) for dynamic logic control. (Completed May 7, 2026)
- [ ] **System Integrity:** Build a "Critical Heartbeat" sensor using the `critical` label to monitor essential infrastructure (Freezer, Networking, Z-Wave).

## 5. Future AI & Occupancy Enhancements
- [ ] **Vision-Based Occupancy Pilot:** Develop a "Master Occupancy Verifier" script using ROVER-02 (and future cameras) to perform human-presence checks before dousing lights.
    - *Goal:* Filter out "Cat Noise" and prevent turn-offs on stationary humans.
- [ ] **Multi-Modal Strategy:** Research a hybrid approach for non-camera rooms (e.g., combining PIR with appliance states or interactive signifiers).
- [ ] **Vision AI Expansion:** Explore using the parlor/kitchen vision pattern for more complex occupancy sensing (e.g., distinguishing between owners and guests).
- [ ] **Natural Language Control:** Expand the `ai_task` timer parser to handle more complex scheduling requests via actionable notifications.

## 6. Legacy Device Bridging (Broadlink RF/IR)
- [ ] **Office Mini-Split Integration:** Use Broadlink RM4 Mini + SmartIR to convert the "dumb" MrCool unit into a `climate` entity.
    - *Logic:* Link to `sensor.office_temperature` for state feedback.
    - *Goal:* Integrate with Eco Mode and Office occupancy.
- [ ] **RF Infrastructure:** Deploy Broadlink RM4 Pro to bridge non-smart RF devices (fans/blinds) into the MBR v7.x logic.
- [ ] **Maintenance Audit:** Transition battery monitoring to the native 2026.5 Maintenance Dashboard.
