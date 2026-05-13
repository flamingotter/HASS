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
- [x] **v7.4 Release:** Implemented "Total Transparency" mode with AI qualitative analysis and unconditional session reporting. (Deployed May 11, 2026)
- [x] **v7.3 Release:** Implemented Data Armor v2 (physical clamps), empirical BigQuery re-baselining, and maximum transparency logging. (Completed May 10, 2026)
- [ ] **Thermal Decay Modeling:** Analyze the first "80F+ Day" to determine if a solar-load offset is needed for pre-cooling start times.
- [ ] **Decommissioning:** Once v7.4 is proven stable, disable the legacy v6.3 automation in the UI to prevent logic overlaps.

## 3. Presence & Global Logic
- [ ] **Eco Mode Validation:** Verify the first real-world 500-mile "Extended Away" trigger.
- [ ] **Proximity Testing:** Confirm both Josh and MJ entering the 50-mile radius correctly releases Eco Mode.

## 4. Maintenance & Housekeeping
- [x] **Notification Standardization:** Standardized `Notify: Feed Pets (v3.0)` and `Notify: Trash Day` using the "Detective Butler" device ID pattern. (Completed May 12, 2026)
- [x] **Climate Integrity:** Implemented "The Learning Gate," Short-Cycle protections, and the "Unbreakable Latch" in MBR Engine v7.7. (Completed May 13, 2026)
- [x] **Total Transparency:** Deployed verbose mobile notifications and AI reasoning logs for all climate phases. (Completed May 13, 2026)
- [x] **Precision Math:** Fixed 60-minute duration drift by switching to native epoch timestamps. (Completed May 13, 2026)
- [x] **Continuous Logic Validation:** Established the "Sim Lab" for regression testing. (Completed May 13, 2026)
- [ ] **System Integrity:** Build a "Critical Heartbeat" sensor using the `critical` label to monitor essential infrastructure (Freezer, Networking, Z-Wave).
- [ ] **Notification Standardization (Remaining):** Refactor `Person: Status Synchronizer`, `Garage Door Monitor`, and `Maintenance Engine` to use the unified `activate_mobile_actionable_notification` script.

## 5. Future AI & Occupancy Enhancements
- [ ] **Digital Twin Analysis:** Perform first correlation analysis (Door Open/Occupancy vs. Cooling Rate) once 7 days of new BigQuery data is collected.
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
