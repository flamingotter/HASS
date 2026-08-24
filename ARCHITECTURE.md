# Home Assistant Lab: System Architecture

## System Mission
The **Home Assistant Lab** is a production-grade, whole-home automation ecosystem engineered for extreme environmental precision, AI-augmented reasoning, and comprehensive infrastructure resilience. By synthesizing high-frequency sensor data, cloud-scale analytics (BigQuery), and local AI co-processing, the system transforms a standard residence into a reactive, data-driven environment that prioritizes resident comfort, physical safety, and operational transparency.

---

## 1. Core Engineering Mandates
- **Modular Config:** The system uses `packages:` for integrations and `!include_dir_list` for entities.
- **Explicit Types:** Jinja templates MUST explicitly cast variables (e.g., `| float`, `| int`, `| string | trim`) to prevent Home Assistant's automatic type-guessing from corrupting data.
- **Fail-Safe AI:** Any automation relying on `ai_task` must provide local fallback defaults and use `continue_on_error: true`.

---

## 2. Presence & Eco Mode
**Authority:** `Person: Status Synchronizer`
The system manages occupancy via a centralized "Authority" state machine.

- **Eco Mode:** Triggered by `input_boolean.eco_mode`.
    - **Activation:** Josh or MJ cross 500-mile radius OR 24-hour absence.
    - **Deactivation:** BOTH residents cross back within 50-mile radius.
- **Reaction:** When Eco Mode is ON, the Climate Engine switches to pet-safe targets (66°F Heat / 74°F Cool) and non-critical automations are suppressed.

---

## 3. MBR Climate Engine (v7.8.6)
A high-precision engine designed to reach sleep temperature exactly at bedtime.

- **Data Repository:** `input_text.mbr_cooling_performance_data` (JSON). Stores min/deg cooling rates in 5-degree outdoor bins up to 100°F (`90`, `95`, and `100` bins added June 2026 to prevent silent lookup fallback failures on hot afternoons/evenings).
- **Single-Pass Clean-Sweep Pattern:** Consolidated logic (Load -> Normalize -> Lookup -> Math -> Merge) inside a single Jinja block to eliminate duplicate keys and type-drift.
- **Safety-First Handoff:** Thermostat reset to maintenance target occurs at the **absolute start** of Phase 3. This ensures that even if learning math or AI co-processing fails, the home remains at a safe temperature.
- **Atomic Lock (Mode: Queued):** The automation uses `mode: queued`. Because the thermostat is reset first in Phase 3 (v7.8.4 hardening), any subsequent "zombie" triggers in the queue will find the state no longer matches the "Agonal Push" requirement (T6 target is no longer 60°F) and stop safely. This mode ensures that 7:00 AM wakeup and AI evaluations are not interrupted by sensor jitter.
- **Adaptive Learning Velocity:** Implemented in v7.8.6. The engine automatically shifts its learning weight based on data convergence:
    - **Aggressive (70/30):** Used when the new observation differs from the repo by > 3.0 min/deg. Allows rapid adaptation to seasonal shifts.
    - **Stable (90/10):** Used when the observation is within the ballpark of the repo. Prevents jitter and locks in "solid averages."
- **Phases & Lean Notification Architecture:**
    1. **Wakeup (7:00 AM):** Reset downstairs thermostat to neutral (70°F trial). Silent execution with diagnostic file log.
    2. **Strategist (7:00 PM):** Actionable Free Cooling gate. Evaluates outdoor temperature (at least 3°F cooler than bedroom) and outdoor humidity (< 65%). Only pushes a mobile alert if opening the patio door is actually beneficial; otherwise remains completely silent.
    3. **Pre-Cooling:** Aggressive push based on bin math + AI Humidity Optimizer. Sends single pre-cooling initiation notification with ETA.
    4. **Handoff:** At target or bedtime, reset T6 Pro to maintenance temp. AI Auditor validates session data. Routine handoff and learning updates run silently; alerts sent only if an anomaly is detected.
    5. **Sleep Window Maintenance (Overnight):** Maintains bedroom within ±1°F deadband completely silently.
- **Data Armor:** A software physical-swing cap protects the repository from sensor jitter or thermal anomalies. **Raised to 60.0 min/deg** to accommodate extreme summer heat loads.
- **Bedtime Shift & Solar Pressure Relief (Added June 2026):** Shifting the sleep bedtime target to `23:30` (11:30 PM) places pre-cooling triggers later in the evening (typically 7:30 PM - 8:30 PM). This delays the start of the high-draw cycle until after solar radiation on the roof deck has subsided, bypassing peak attic heat-soak loads, enhancing thermal decay efficiency, and ensuring virtually 100% comfort target reliability.
- **Target Override Safeguard (Added June 2026):** To prevent accidental target temperature changes (such as slider touches while scrolling on mobile devices) from disrupting the active pre-cooling cycle, a state-recalculating safeguard was implemented. It monitors target temperature updates during pre-cooling, sends an actionable push notification with options to keep or revert the change, and handles the revert state statelessly using dynamic callback actions (REVERT_BEDROOM_TARGET_XX).
- **Attic Micro-Climate Sensors (Added June 2026):** Two physical dual-sensor arrays were integrated to capture real-time roof thermal loads:
    - **North Attic:** `sensor.north_attic_sensor_air_temperature` / `sensor.north_attic_sensor_humidity`. Covers the front porch, dining area, foyer, laundry, pantry, and north guest room. Mounted 2 feet above blown-in insulation, 1 foot below the roof deck.
    - **South Attic:** `sensor.south_attic_sensor_air_temperature` / `sensor.south_attic_sensor_humidity`. Covers the living room and downstairs master bedroom suite. Mounted 2 feet below the highest peak of the roofline.
    - **Physical Separation:** The two attic zones are separated by the second-floor hallway and office, with a small connecting space above the hallway.
- **Thermodynamic Solar Load Asymmetry (SLA):** Under midday solar exposure, an intense thermal gradient exists across the roof. Telemetry shows a 14.6°F asymmetric solar load delta between the South Attic (112.1°F) and the North Attic (97.5°F), creating a 45.6°F thermal conduction differential across the downstairs MBR ceiling (66.5°F indoor room temperature).
- **Roadmap to Climate Engine v7.9:** Mapped inside `exporter.py` for 7-day high-resolution BigQuery baseline profiling. Once complete, Scenario K (Attic Heat Soak Challenge) will validate the model in Sim Lab, allowing real-time attic thermal pressure to be used as a dynamic pre-cooling start-time multiplier.
- **Whole-Home Climate Coordinator (v1.0 - August 2026):** Unified, all-season thermal orchestration for both Trane central heat pumps:
    - **Downstairs (`climate.t6_pro_downstairs`):**
        - *Cooling:* 70°F Daytime neutral baseline (7:00 AM reset); evening/night sleep comfort managed dynamically by Sleep Comfort Engine v7.8.6.
        - *Heating:* 68°F Daytime & Evening (7:00 AM – Bedtime), 64°F Overnight Setback (Bedtime – 7:00 AM), 66°F Eco Mode.
    - **Upstairs (`climate.t6_pro_upstairs`):**
        - *Cooling:* 73°F Daytime & Evening, 76°F Overnight Setback, 78°F Eco Mode (with independent office mini-split at 68°F Auto).
        - *Heating:* 67°F Daytime & Evening, 62°F Overnight Setback, 64°F Eco Mode.
    - **Eco Mode Restoration:** Mode-aware return logic restoring appropriate seasonal targets (Cool: 70°F / 73°F; Heat: 68°F / 67°F).



## 4. Whole-Home Appliance Intelligence & Consumables Engine
**Authority:** `Appliance: Cycle and Consumables Tracker` (`id: appliance_cycle_and_consumables_tracker`)
Monitors high-draw major appliances using circuit-level Emporia Vue 3 telemetry and smart plugs.

- **Washing Machine:** `binary_sensor.washing_machine_running` (Active $> 4\text{W}$, 2-min debounce off). Sends push notification to transfer laundry and auto-decrements `input_number.laundry_detergent_loads_remaining`.
- **Clothes Dryer:** `binary_sensor.clothes_dryer_running` (Active $> 30\text{W}$, 5-min debounce off to bridge sensor-dry moisture pauses). Sends push notification when drying cycle completes.
- **Dishwasher:** `binary_sensor.dishwasher_running` (Native `sensor.dishwasher_operation_state` == `run` with $> 10\text{W}$ CT fallback, 1-min debounce off). Sends push notification when cycle completes and auto-decrements `input_number.dishwasher_tabs_remaining`.
- **Consumables Depletion Alerts:** Pushes a low-stock alert when remaining detergent loads or dishwasher tabs reach $\le 5$.
- **1-Tap Dashboard Restock:** Physical/Lovelace button triggers (`input_button.reset_laundry_detergent` and `input_button.reset_dishwasher_tabs`) dynamically read from configurable package size helpers (`input_number.laundry_detergent_restock_quantity` [default 96] and `input_number.dishwasher_tabs_restock_quantity` [default 60]) to instantly refresh inventory counts.

---

## 5. Vision & Security Engine (v1.5)
**Authority:** `Security: Front Porch - AI Video Analysis`
Handles identity verification and suspicious activity detection.

- **Resilient Recording:** Uses `continue_on_error: true` for `camera.record` to survive DTS stream errors (caused by 5s GOP intervals found in camera hardware).
- **Sequential Processing:** Data collection (video/snapshots) must complete and include a 2s "Flush Delay" before AI analysis begins to prevent file-locking errors.
- **AI Context:** Uses MJ and Josh reference photos to identify residents vs. delivery personnel.
- **Patio Camera Detection Synchronization:** Person and animal smart detections (`switch.patio_left_detections_person`, `switch.patio_left_detections_animal`, `switch.patio_right_person_detection`, `switch.patio_right_animal_detection`) are dynamically coordinated across routines:
  - *Awake / Home:* Suspended (`off`) upon `MBR Wakeup` and arriving home (`disarmed` from away) to suppress nuisance notifications and footage during daily outdoor activities.
  - *Bedtime / Overnight:* Re-enabled (`on`) upon `MBR Bedtime` (`alarm_arm_night`) for nocturnal perimeter protection.
  - *Away:* Re-enabled (`on`) whenever the alarm transitions to `armed_away` / `armed_vacation`.

---

## 6. Whole-Home Energy Architecture (Emporia Vue 3)
**Hardware:** Dual ESPHome-flashed Emporia Vue 3 units (`emporiavue3_panel_01` and `emporiavue3_panel_02`).
- **Feeder Standard:** Phase A (Left Main / Black Voltage Wire) and Phase B (Right Main / Red Voltage Wire) across both 200A panels.
- **Circuit Hierarchical Aggregates:** Defined in `entities/templates/sensor.energy_hierarchical_aggregates.yaml` (calculating Grid Total, 1st/2nd Floor Totals, Kitchen, IT/Office, Living, and HVAC/Utility subsystems).
- **Appliance Cycle Interlocks:** Real-time current/power feeds `binary_sensor.washing_machine_running`, `binary_sensor.clothes_dryer_running`, and `binary_sensor.dishwasher_running`.
- **Calibration Baseline Cutoff:** Formally calibrated on **August 22, 2026 at 17:13:00 UTC** (Panel 02) and **August 24, 2026 at 13:35:00 UTC** (Panel 01). Historical queries prior to these timestamps contain uncalibrated/inverted data; all whole-home BigQuery analytics and baseline modeling should filter `timestamp >= '2026-08-24T13:35:00Z'`.

---

## 7. Analytics & Infrastructure
- **BigQuery Pipeline:** Data is exported to BigQuery for thermal decay, energy modeling, and cooling velocity analysis. The `ha_bq_exporter` container is hardened with an infinite sleep loop (`sh -c "python exporter.py; exec sleep infinity"`) and set to `restart: unless-stopped`. This keeps the container permanently in a `Running` state to prevent it from being pruned by the weekly `docker system prune` of the housekeeper, while allowing Home Assistant to trigger the daily export cleanly via the `socket-proxy` restart command.
- **AI Agent Direct Query (Remote MCP):** To empower AI agents with direct, real-time analytics access, the official Google Cloud remote MCP server (`bigquery_remote`) is integrated client-side. This allows direct, credential-secured schema discovery and querying against the `moonlit-botany-293421` project's `home_assistant_data` dataset.
- **Docker Management:** Container control is handled via `curl` to the `socket-proxy` Docker API.
- **Sim Lab:** A Digital Twin environment (`integrations/sim_lab.yaml`) used to stress-test logic against 10 specific scenarios (e.g., Short-Cycle, Type Mismatch, High Humidity) before deployment.

---

## 8. Diagnostic Cheat Sheet
- **Climate Check:** `grep "PHASE_" climate_control_log.csv | tail -n 20`
- **Simulation Validation:** `grep "SIM_DATA" home-assistant.log | tail -n 10`
- **Docker Status:** `curl -s http://127.0.0.1:2375/containers/ha_bq_exporter/json | jq .State.Status`
- **Config Check:** `ha core check` or `ha core restart`

---

## 7. Custom Agent Skills Suite
To empower programmatic, local, and secure AI-agent operations, the system deploys a suite of local Python-executable tools in the `skills/` directory. These tools are designed with zero external host-level dependencies to execute natively on the host's standard Python interpreter (`/usr/bin/python3`), while utilizing secure credential parsing or container-delegation pathways for privileged operations.

### Component Map

#### A. HA REST API Client (`skills/ha_client.py`)
A lightweight, programmatic REST client that extracts Bearer Tokens and internal endpoints directly from `/root/.gemini/antigravity-cli/mcp_config.json`. This tool bypasses SQL database queries to interact directly with Home Assistant's state engine and services.
* **Usage - Fetch State:** `python3 skills/ha_client.py get sensor.bedroom_temperature_smoothed`
* **Usage - Call Action:** `python3 skills/ha_client.py action light turn_on '{"entity_id": "light.bedroom_ceiling"}'`

#### B. Jinja Sandbox Compiler (`skills/jinja_sandbox.py`)
A secure sandboxed parsing and compilation engine that compiles arbitrary Jinja templates using Home Assistant's native `/api/template` REST endpoint. This ensures accurate type evaluation and system variable lookups without running local sandbox parsers.
* **Usage:** `python3 skills/jinja_sandbox.py "{{ states('sensor.bedroom_temperature_smoothed') | float }}"`

#### C. Log Diagnostic & Performance Compiler (`skills/log_parser.py`)
A streaming parser that scans `climate_control_log.csv` and `home-assistant.log`. It isolates core events (`PHASE_`), highlights climate exceptions, and compiles SQLite database lock/warning metrics into formatted CLI tables.
* **Usage - Climate Phase Logs:** `python3 skills/log_parser.py --type climate`
* **Usage - System Lock/Errors:** `python3 skills/log_parser.py --type errors`

#### D. BigQuery Container Delegate (`skills/bq_analytics.py`)
A host-side delegate script. Because the host lacks GCP Python packages, this delegate pipes SQL queries and options via `docker exec ha_bq_exporter` to query BigQuery using `/app/service-account.json` inside the running container. This provides zero-dependency, rapid SQL execution on the host.
* **Usage:** `python3 skills/bq_analytics.py --preset SLA_ASYMMETRY`

#### E. Sim Lab Scenario Runner & Learning Auditor (`skills/run_sim_lab.py`)
An automation runner that triggers digital twin scenarios in the Sim Lab (`script.run_climate_stress_tests`) and audits repository learning state transitions (`input_text.sim_mbr_repo`) to verify math and adaptive learning velocity changes after simulation runs.
* **Usage:** `python3 skills/run_sim_lab.py --scenario 1`

