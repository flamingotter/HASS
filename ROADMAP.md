# Development Roadmap

This document tracks active projects, pending infrastructure fixes, and long-term goals for the Home Assistant deployment.

---

## 1. Immediate Infrastructure & Hardware Fixes
- [x] **Bluetooth Stability:** Host-level settings updated May 6, 2026. Monitoring for stability.
- [x] **Porch Cameras:** Diagnosed `Errno 22` video recording errors as DTS drift caused by 5s GOP interval (nMultiplier: 5). Implemented software failsafe in AI Analysis v1.5 (sequential processing + flush delay) to ensure logic continuity when stream jitter occurs. (Completed May 14, 2026)
- [x] **BigQuery Integration:** Re-created `bq_venv`, verified `hvac_health_check.py` functionality, and hardened credentials path. (Completed May 6, 2026)
- [ ] **Hardware Maintenance:** 
    - Re-add `light.masonic_lamp` to the network.
    - Physical install and entity update for `binary_sensor.bedroom_door` (replaces `binary_sensor.bedroom`).

## 2. Climate & Energy (The Sleep Engine v7.x)
- [x] **High-Temperature Bin Expansion & Bedtime Shift:** Expanded repository to include `90`, `95`, and `100` temperature bins (up to 60.0 min/deg) to handle high-temperature afternoon/evening pre-cooling. Shifted bedroom sleep bedtime target to `23:30` (11:30 PM) to move the aggressive AC cycle to late evening after solar roof pressure decays, maximizing thermal efficiency and comfort reliability (Completed June 11, 2026).
- [x] **v7.9.0 - BigQuery Autonomous HVAC Calibration (Shadow Mode):** Created a dedicated, container-side calibration agent (`mbr_auto_calibrate.py`) and a new shadow helper (`input_text.mbr_cooling_performance_shadow_data`). The agent queries 30 days of pre-cooling sessions from BigQuery, reconstructs evening runs, applies Data Armor physical limits, runs a linear regression trend line to extrapolate missing temperature bins, and autonomously updates the shadow repository weekly for dry-run validation (Completed July 23, 2026).
- [x] **Bedtime Target Hardening & Dynamic Ramping Strategy:** Confirmed that the pre-cooling engine, AI Auditor, and binary sensors are fully dynamic and adapted instantly to the new $65^\circ\text{F}$ bedtime target (formerly $64^\circ\text{F}$). Designed a dynamic setpoint ramping strategy for the single-stage Trane 2.5-ton first-floor heat pump to replace thermostat-slamming (setting T6 to $60^\circ\text{F}$) and allow the compressor to take natural, healthy rest cycles (Completed July 23, 2026).
- [x] **AI Auditor Temperature-Awareness Hardening:** Identified a bias where the AI Auditor rejected high-temperature runs (such as 81.1 min/deg and 84.0 min/deg on 90F+ days) as anomalies. Restructured the automation to pass real-time average outdoor temperature to the Auditor and clarified that 45-90 min/deg rates are expected and valid under extreme heat-soak loads, enabling high-temperature bins (90, 95, 100) to successfully refine (Completed July 22, 2026).

- [x] **v7.8.6 Release:** Adaptive Learning Velocity. Implemented automatic weight-shifting (90/10 vs 70/30) based on data convergence (Completed May 29, 2026).
- [x] **v7.8.5 Release:** Summer Resilience. Restored `mode: queued` with Atomic Lock, raised Data Armor cap to 60.0, and implemented Humidity-Aware strategist (Completed May 24, 2026).
- [x] **v7.4 Release:** Implemented "Total Transparency" mode with AI qualitative analysis and unconditional session reporting. (Deployed May 11, 2026)
- [x] **v7.3 Release:** Implemented Data Armor v2 (physical clamps), empirical BigQuery re-baselining, and maximum transparency logging. (Completed May 10, 2026)
- [x] **Thermal Decay & Attic Modeling:** Switched from a generic outdoor temperature offset to direct micro-climate monitoring with dual attic sensors (Completed June 2026).
- [x] **Target Override Safeguard:** Added an override protection automation with high-priority actionable mobile notifications to revert accidental slider modifications during pre-cooling (Completed June 8, 2026).
- [x] **Decommissioning:** Completely removed the retired legacy v6.3 automation to prevent background logic overlaps (Completed May 2026).
- [x] **Whole-Home Climate Coordinator (v1.0) & Seasonal Eco Mode Hardening:** Automated dual-floor Trane central heat pumps across all 4 seasons with mode-aware Eco Mode restoration, 70°F daytime cooling baseline, 68°F day / 64°F night heating downstairs, and 67°F day / 62°F night heating upstairs (Completed August 18, 2026).

- [x] **Local BigQuery MCP Server Integration:** Implemented stdio MCP server (`skills/bq_mcp_server.py`) and configured `mcp_config.json` to allow direct, permission-less AI querying of the BigQuery analytics dataset (Completed August 18, 2026).
- [x] **COP-Based Multi-Zone HVAC Health Monitor (BigQuery):** Upgraded `bin/hvac_health_check.py` and `sensor.hvac_health_status` from legacy single-thermostat runtime minutes to full multi-zone electrical energy telemetry using Emporia Vue 3 circuit power (`sensor.panel_01_upstairs_heat_pump_power`, `sensor.panel_02_downstairs_heat_pump_power`). Correlates compressor power (>300W), cycle duration, outdoor ambient temperature, and indoor temperature drop ($\Delta T$) into true $\text{kWh / } ^\circ\text{F drop}$ metrics and 7-day vs baseline degradation tracking for both Upstairs and Downstairs zones. Integrated with standardized actionable mobile alerts via `script.activate_mobile_actionable_notification` (Completed August 24, 2026).
- [ ] **v7.9 Release - Attic Thermal Integration:** Gather a 7-day high-resolution logging baseline for `sensor.north_attic_sensor_air_temperature` and `sensor.south_attic_sensor_air_temperature` in BigQuery, define Scenario K (Attic Heat Soak Challenge) in Sim Lab, and implement a dynamic pre-cooling start-time multiplier based on real-time roof solar gain pressure.


## 3. Presence & Global Logic
- [ ] **Eco Mode Validation:** Verify the first real-world 500-mile "Extended Away" trigger.
- [ ] **Proximity Testing:** Confirm both Josh and MJ entering the 50-mile radius correctly releases Eco Mode.
- [x] **Eco Mode Proximity Reset Hardening:** Added a guard condition to the Enhanced Eco Mode Manager proximity reset logic to verify input_boolean.eco_mode is 'on', preventing unexpected temperature overrides of regular sleep windows when Eco Mode is off (Completed June 23, 2026).

## 4. Maintenance & Housekeeping
- [x] **Notification Standardization:** Standardized `Notify: Feed Pets (v3.0)` and `Notify: Trash Day` using the "Detective Butler" device ID pattern. (Completed May 12, 2026)
- [x] **Climate Integrity v7.8.6:** Hardened Phase 3 logic with "Safety-First Handoff" and "Atomic Lock" (Mode: Queued). Implemented Adaptive Velocity learning. (Completed May 29, 2026)
- [x] **Log Noise Reduction:** Removed `monitor_docker` integration; migrated BigQuery kickoff to surgical `shell_command` via `socket-proxy`. (Completed May 14, 2026)
- [x] **Continuous Logic Validation:** Established the "Sim Lab" with 10-scenario stress test suite. (Completed May 14, 2026)
- [x] **Pantry Door Hardening:** Fixed template and state-filtering runtime errors in the pantry light automation to ignore attribute-only changes and startup/offline states. (Completed June 8, 2026)
- [x] **Custom Agent Skills Suite:** Designed, built, and verified a programmatic, secure Python-based custom skills suite in the `skills/` directory: `ha_client.py` (Home Assistant REST client), `jinja_sandbox.py` (Jinja compiler), `log_parser.py` (log analyzer/diagnostics compiler), `bq_analytics.py` (container-delegated BigQuery analytics engine), and `run_sim_lab.py` (digital twin scenario runner & repository learning auditor). (Completed June 12, 2026)
- [x] **Garage Door Trigger Hardening:** Hardened chimes and door monitor automations with 'from: off' boundaries to eliminate false alerts during wireless sensor drops. (Completed June 8, 2026)
- [x] **BigQuery Pipeline Recovery:** Rebuilt the bq_exporter image and re-created the container after it was pruned by the weekly system pruner. Hardened the container with a sleep loop to prevent future prunes. (Completed June 9, 2026)
- [x] **Remote BigQuery MCP Server Setup:** Configured official Google Cloud remote MCP server (`bigquery_remote`) in `mcp_config.json` with scopes for BigQuery to allow direct, secure AI-agent query and schema-inspection capabilities (Completed June 11, 2026).
- [x] **Alarm panel functions & welcome script hardening:** Hardened the disarmed transition template guard against null-state crashes, trimmed the redundant unhandled disarm trigger, and implemented a robust, whitespace-hardened fail-safe fallback for the AI debrief message (Completed June 12, 2026).
- [x] **Asymmetric Away Alarm Arming Support:** Restructured the arming choose-block in the alarm panel functions automation to natively support mixed presence states, securing the house when residents are in any combination of Away, Extended Away, or Work (Completed June 23, 2026).
- [x] **Door Locks Binary Sensor Modernization:** Updated the Door Locks binary sensor state template to dynamically monitor the centralized `lock.door_locks` group helper instead of only checking a single lock, ensuring aggregate security state tracking across all front, garage, and bedroom doors (Completed June 27, 2026).
- [x] **Yale Lock State Protection:** Hardened MBR Bedtime and Away arming automations with a strict state template guard filtering exclusively for `unlocked` entities and added `continue_on_error: true` to prevent physical bridge offline or upstream yalexs exceptions from blocking critical bedtime/away logic sequences (Completed July 16, 2026).
- [x] **Hallway Light Control (Virtual 3-Way) & Sankey Energy Flow Optimization:** Configured instant control for `light.hall_light` via dual Zooz ZEN73 switches (`switch.hall_switch_01` and `switch.hall_switch_02`) set to local/Z-Wave control disabled. Streamlined the energy dashboard Sankey flow into a clean 4-column layout with `Garage Main` and `Garage Extension` as intermediary Section 2 nodes, placing `Beer Fridge` and `Freezer` inline with all appliances/devices, reordering child nodes to eliminate crossing lines, and enabling `show_remaining: true` (Completed August 14, 2026).
- [x] **Catio Light Control (Virtual 3-Way & LIFX Smart Bulb Integration v2.0):** Configured Zooz ZEN73 switches (`switch.catio_light_01`, `switch.catio_light_02`, `switch.catio_light_03`) with Parameter 10 = 1 (Scene Control) and Parameter 12 = 2 (Local & Z-Wave Relay Disabled) to maintain uninterrupted 120V power to dual LIFX smart bulbs (`light.catio_lifx_01`, `light.catio_lifx_02`). Implemented `Light Control: Catio (v2.0)` in `automations.yaml` handling multi-tap gestures: Single-Tap UP (100% 4500K), Double-Tap UP (20% Colorloop), Double-Tap DOWN (4500K effect-stop preserving brightness), and Single-Tap DOWN (All OFF) with full guide-light LED synchronization (Completed August 22, 2026).
- [x] **Garage Entry Light Control (Virtual 3-Way ZEN73 + ZEN12):** Created virtual 3-way synchronization between single-pole `switch.garage_entry_switch` (ZEN73) and virtual companion `light.garage_motion_switch` (ZEN12 motion switch wired power-only). Supports physical Z-Wave Central Scene button events and HA state triggers using `homeassistant.turn_on` / `homeassistant.turn_off` cross-domain targets (Completed August 16, 2026).
- [x] **Downstairs Hallway & Dining Room Smart Bulb Switch Synchronization:** Implemented `Light Control: Downstairs Hallway (v1.0)` and updated `Light Control: Dining Room (v2.0)` to maintain full guide-light LED synchronization (LED OFF when lights ON, LED ON when lights OFF) across dual Zooz ZEN73/ZEN74 switches in Smart Bulb Mode (Completed August 21, 2026).
- [x] **Kitchen Controller (3x ZEN35) LED Synchronization Hardening:** Completely refactored `script.update_kitchen_zen35_leds` and `Kitchen Controller - All Devices & LED Sync (v3.0)` with Jinja delta-state filtering (`reject('is_state', ...)`), whitespace-hardened templates (`| trim`), `mode: queued` execution, and paced Z-Wave radio delivery to eliminate Z-Wave packet collisions, race conditions, and out-of-sync LEDs across all 3 keypads (Completed August 21, 2026).
- [x] **Patio Camera Smart Detection Synchronization (Person & Animal):** Coordinated UniFi Protect smart detection switches across Patio Left and Patio Right (`switch.patio_left_detections_person`, `switch.patio_left_detections_animal`, `switch.patio_right_person_detection`, `switch.patio_right_animal_detection`). Suspends detection during waking hours at home (via `MBR Wakeup` and returning home `disarmed` from away), and re-enables detection for perimeter security during `MBR Bedtime` (`alarm_arm_night`) and `Armed Away` (Completed August 24, 2026).
- [x] **Notification Standardization & Dismissal Hardening:** Hardened `script.activate_mobile_actionable_notification` to dynamically build actions arrays (0–3 buttons), support critical alarm streams, sticky/persistent flags, and thread tags. Audited and hardened all actionable automations (`Notify: Feed Pets (v3.0)`, `Notify: Trash Day`, `Notify Shuttle Bay`, `Door Security: Safety & Armed Alerts`, `Notify House Guests`, `Alarm Panel Functions`, `System: Maintenance Engine (v2.0)`, `Cleaning Lifecycle`, `Climate: Enhanced Eco Mode Manager (v2.0)`, and `Appliance: Cycle and Consumables Tracker`) with operational state guards, companion tag separation (e.g. `*-status` vs `*-notify`), and multi-device `clear_notification` broadcasts to prevent loop triggers and unintended AI nags upon notification dismissal (Completed August 26, 2026).
- [ ] **System Integrity:** Build a "Critical Heartbeat" sensor using the `critical` label to monitor essential infrastructure (Freezer, Networking, Z-Wave).

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

## 7. Whole-Home Energy & Utility Intelligence (Emporia Vue 3)
### 🔍 Phase 7.1: Data-First Observation & Baseline Analysis
- [x] **Energy Exporter Integration:** Mapped all 29 Emporia Vue 3 channels and dual attic sensors in `exporter.py`, verified 518k-row staging/merge pipeline into BigQuery (Completed August 19, 2026).
- [x] **Emporia Vue 3 Hardware Calibration & Phase Alignment:** Completed on-panel CT clamp rewiring and ESPHome phase alignment on August 22, 2026 for Panel 02 and August 24, 2026 (13:35 UTC / 9:35 AM EDT) for Panel 01.
    - *Hardware Fixes:* Isolated single hot leg on 240V Water Heater 30A circuit (eliminating magnetic cancellation) and reseated Dishwasher clamp.
    - *ESPHome Phase Calibration:* Standardized Phase A (Left Feeder / Black wire) and Phase B (Right Feeder / Red wire) on Panel 01 and Panel 02. Aligned branch circuit `phase_id` mappings across both panels to eliminate 180° negative power truncation by the `*pos` filter.
    - *Telemetry Validation:* Verified active draws on all 29 channels; Panel 01 branch circuit sum (1,109.7 W) matches 200A mains (1,110.7 W) within 0.09% deviation.
    - *Analytics Note:* **All whole-home BigQuery energy models, baseline calculations, and COP analytics should use data recorded on or after `2026-08-24T13:35:00Z` for 100% calibrated accuracy across all circuits.**
- [ ] **14-Day Baseline Profiling:** Log real-world curves (starting August 22, 2026 post-calibration) to analyze unmanaged peak demand patterns, baseline household "phantom" standby loads, and signature well pump runtimes before purchasing hardware.
- [x] **Washer & Dryer Cycle Tracker:** Implemented power-draw template binary sensors (`binary_sensor.washing_machine_running`, `binary_sensor.clothes_dryer_running`), laundry completion push notifications to Josh & MJ, and predictive detergent pod depletion counter with low-stock alerts and 1-tap reset (Completed August 19, 2026).
- [x] **Dishwasher Consumables Predictor:** Implemented power-draw wash cycle detection (`binary_sensor.dishwasher_running`), completion notifications, and auto-decrementing tab counter with <= 5 tab low-stock alert and 60-tab dashboard reset button (Completed August 19, 2026).

### 🛡️ Phase 7.2: Decentralized Physical Load Management
- [ ] **Garage Node (Water Heater Peak-Shedding):** Install a UL-listed **Zooz ZEN78 High-Power 40A Relay** next to the garage water tank to safely break both L1/L2 legs simultaneously and support manual push-button overrides.
- [ ] **Crawl Space Node (Well Pump & Leak Shield):** Install a **Zooz ZEN17 Universal Relay** in the crawl space near the pressure tank.
    - *Relay 1:* Act as the emergency well pump cutoff switch (triggered on 20-minute continuous run cycles).
    - *Input 1:* Wire a low-voltage floor leak probe to locally trigger well-pump shutdown if a pipe drips.
- [ ] **HVAC COP-Based Health Monitor:** Program a weekly auditor inside BigQuery correlating compressor kW-draw with temperature drops to proactively detect degraded heat-pump performance.
- [x] **Cross-Floor Thermal Balancing:** Created unified `Climate: Whole-Home Thermostat Coordinator (v1.0)` interlocking Upstairs and Downstairs T6 Pro thermostats across all seasons with Eco Mode sync and stack-effect mitigation (Completed August 18, 2026).
- [ ] **Integrated Vacation Load-Shedding:** Automate non-essential smart plugs and water-heater power-downs the moment the system registers "Extended Away" status.

