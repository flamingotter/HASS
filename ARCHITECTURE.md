# Home Assistant Lab: System Architecture

## System Mission
The **Home Assistant Lab** is a production-grade, whole-home automation ecosystem engineered for extreme environmental precision, AI-augmented reasoning, and comprehensive infrastructure resilience. By synthesizing high-frequency sensor data, cloud-scale analytics (BigQuery), and local AI co-processing, the system transforms a standard residence into a reactive, data-driven environment that prioritizes resident comfort, physical safety, and operational transparency.

---

## 1. Core Engineering Mandates
- **Modular Config:** The system uses `packages:` for integrations and `!include_dir_list` for entities.
- **UI-First Helper Provisioning:** Helper entities (`input_text`, `input_boolean`, `input_number`, `input_datetime`, `timer`) are provisioned via Home Assistant's collection WebSocket API (`<domain>/create`) rather than YAML files, ensuring they remain native UI-editable helpers in `.storage/`.
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
- **Guest Presence State:** Keypad credential unlocks (`event.home_locks_*`) automatically activate `input_boolean.house_guests`, reflect `House Guests` state in `sensor.home_status`, disarm the security perimeter, illuminate guest paths, and adjust Kitchen Adaptive Lighting night floors.
- **Micro-Occupancy Engine (`binary_sensor.josh_in_office`):** Employs Bermuda BLE beacon distance estimation ($\le 18.0\text{ ft}$ with a 30s debounce delay) to verify Josh's localized desk presence in the second-floor office.

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
- **Multi-Zone COP HVAC Health Engine & Real-Time Runaway Sentinels:**
    - **Physical Zone Mapping:**
        1. *Downstairs Zone (Floor 1):* `sensor.panel_02_downstairs_heat_pump_power` vs `climate.t6_pro_downstairs` (Master Bedroom Suite & Great Room).
        2. *Upstairs Zone (Floor 2):* `sensor.panel_01_upstairs_heat_pump_power` vs `climate.t6_pro_upstairs` (Hallway, Guest Bedroom, Bonus Room).
        3. *Office Mini-Split (Floor 2):* `sensor.panel_01_mini_split_power` vs `sensor.office_sensor_air_temperature` (Isolated Office / Server Corner).
    - **Batch Health Engine (`bin/hvac_health_check.py`):** Calculates true thermodynamic $\text{kWh / } ^\circ\text{F drop}$ across all 3 zones with `MIN_SAMPLE_CYCLES = 5` statistical gate, 8–90 min pull-down duration filter, and August 24 calibration cutoff.
    - **Real-Time Runaway Watchdogs:** Instant HA automation sentinels that alert if central compressors run pinned above 1,100W for > 2.5 hours (`hvac_upstairs_runaway_alert`) or if the office mini-split is offline during daytime work hours when office temperature exceeds 77°F (`hvac_office_minisplit_failure_alert`).



## 4. Whole-Home Appliance Intelligence & Consumables Engine
**Authority:** `Appliance: Cycle and Consumables Tracker` (`id: appliance_cycle_and_consumables_tracker`)
Monitors high-draw major appliances using circuit-level Emporia Vue 3 telemetry and smart plugs.

- **Washing Machine:** `binary_sensor.washing_machine_running` (Active $> 4\text{W}$, 2-min debounce off). Sends push notification to transfer laundry and auto-decrements `input_number.laundry_detergent_loads_remaining`.
- **Clothes Dryer:** `binary_sensor.clothes_dryer_running` (Active $> 30\text{W}$, 5-min debounce off to bridge sensor-dry moisture pauses). Sends push notification when drying cycle completes.
- **Dishwasher:** `binary_sensor.dishwasher_running` (Native `sensor.dishwasher_operation_state` == `run` with $> 10\text{W}$ CT fallback, 1-min debounce off). Sends push notification when cycle completes and auto-decrements `input_number.dishwasher_tabs_remaining`.
- **Consumables Depletion Alerts:** Pushes a low-stock alert when remaining detergent loads or dishwasher tabs reach $\le 5$.
- **1-Tap Dashboard Restock:** Physical/Lovelace button triggers (`input_button.reset_laundry_detergent` and `input_button.reset_dishwasher_tabs`) dynamically read from configurable package size helpers (`input_number.laundry_detergent_restock_quantity` [default 96] and `input_number.dishwasher_tabs_restock_quantity` [default 60]) to instantly refresh inventory counts.

---

## 5. Notification Architecture & Standardization
**Unified Dispatcher:** `script.activate_mobile_actionable_notification`
Standardizes actionable and informational push notifications across iOS and Android companion apps (`notify.mobile_app_josh_mobile`, `notify.mobile_app_mj_pixel_8_pro`, and `notify.all_devices`).
- **Dynamic Action Generator:** Automatically constructs 0, 1, 2, or 3 interactive action buttons without rendering blank UI buttons when fewer actions are specified.
- **Priority & Critical Channels:** Supports high-priority delivery, custom thread grouping (`notify_tag`), persistent/sticky alerts, TTL expirations, and bypass for phone silent modes (`channel: alarm_stream`).
- **State Guarding on Dismissal:** All automations listening for `mobile_app_notification_cleared` events MUST verify that the underlying operational condition/helper is still active (e.g. `input_boolean.trash_reminder: 'on'`, `input_boolean.feed_pets_reminder: 'on'`, `input_boolean.cleaning: 'on'`, `timer.timer_eco_mode_normal: 'idle'`) to prevent infinite nag loops caused by OS-level dismissal events or action-tap side effects.
- **Tag Separation for Status Acknowledgements:** Status and completion push messages (e.g., `trash-status`, `pets-status`, `eco-status`, `garage-status`, `arm-guests-status`) MUST use discrete tags separated from interactive prompts (`trash-notify`, `pets-notify`, `eco-finish`, `garage-warning_01`, `arm-guests`) so swiping away confirmation notices does not trigger cleared listeners.
- **Cross-Device Dismissal on Completion:** When an actionable task is resolved or delayed, automations broadcast `notify.all_devices` with `message: clear_notification` and target `tag` to cleanly dismiss stale prompts across all household devices.
- **Standardized Consumers:** Fully deployed across `Notify: Feed Pets (v3.0)`, `Notify: Trash Day`, `Notify Shuttle Bay`, `Door Security: Safety & Armed Alerts`, `Notify House Guests`, `Alarm Panel Functions`, `System: Maintenance Engine (v2.0)`, `Cleaning Lifecycle`, `Climate: Enhanced Eco Mode Manager (v2.0)`, and `Appliance: Cycle and Consumables Tracker`.

---

## 6. Vision & Security Engine (v1.7)
**Authority:** `Security: Front Porch - AI Video Analysis` (`automation.ai_porch_intelligence`)
Handles identity verification, visitor triage, and suspicious activity detection at the perimeter.

- **Walkway Approach Trigger:** Exclusively triggered by `binary_sensor.front_porch_ptz_person_detected` to detect approaching visitors early while traversing the front walkway.
- **Dual-Camera AI Coverage:** Simultaneously captures a high-resolution doorbell snapshot (`t0`) and walkway approach MP4 video clip, evaluating both jointly using local `qwen-vl-7b` (staying strictly under 2,300/4,096 tokens).
- **Resilient Recording:** Uses `continue_on_error: true` on `camera.record` and a mandatory 2-second "Flush Delay" before AI processing to survive DTS stream jitter caused by 5s GOP intervals on UniFi cameras without crashing the automation.
- **Cooldown Safeguard:** Enforces a 3-minute visitor event cooldown against `notify.daily_camera_log` to prevent duplicate arrival/departure notifications within short windows.
- **Rolling Media Archive:** Supported by `bin/archive_porch_snapshots.sh` (`integrations/shell.yaml`), maintaining a 3-day rolling history in `/media/snapshots/porch/archive/` preserving full 3-snapshot sequences (`t0`, `t1`, `t3`) and approach video clips with automated disk pruning.
- **Dependency Armor (Extended OpenAI):** Requires `manifest.json` patched to `openai>=2.45.0` (matching HA Core 2026.9.2 pinned version) to prevent integration setup aborts and ensure `extended_openai_conversation.query_image` remains persistently registered.
- **Patio Camera Detection & Security Architecture:** Smart detections on Patio Left and Patio Right cameras remain permanently active 24/7. This guarantees that `binary_sensor.patio_left_person_detected` and `binary_sensor.patio_right_person_detected` remain fully online and responsive to trigger `Lighting: Outdoor Motion Presence` (`switch.backyard_lights`) whenever someone is outside after dark (`sun.sun: below_horizon`), regardless of alarm or waking state.
- **Software-Gated Security Notifications:** Perimeter security alerts for Patio Left and Patio Right are decoupled from hardware sensor power and handled purely at the software logic layer via `Security: Patio Perimeter Alert (Night & Away)`. When the alarm is armed (`armed_night`, `armed_away`, `armed_vacation`) or residents are away, person detection dispatches rich actionable mobile notifications with live camera snapshots, direct UniFi Protect deep-linking (`app://com.ubnt.unifi.protect`), and one-tap backyard floodlight controls. During waking home hours, Protect app notifications for patio cameras are silenced to eliminate daytime notification fatigue while preserving full motion lighting automation.

---

## 7. Whole-Home Energy Architecture (Emporia Vue 3)
**Hardware:** Dual ESPHome-flashed Emporia Vue 3 units (`emporiavue3_panel_01` and `emporiavue3_panel_02`).
- **Feeder Standard:** Phase A (Left Main / Black Voltage Wire) and Phase B (Right Main / Red Voltage Wire) across both 200A panels.
- **Circuit Hierarchical Aggregates:** Defined in `entities/templates/sensor.energy_hierarchical_aggregates.yaml` (calculating Grid Total, 1st/2nd Floor Totals, Kitchen, IT/Office, Living, and HVAC/Utility subsystems).
- **Appliance Cycle Interlocks:** Real-time current/power feeds `binary_sensor.washing_machine_running`, `binary_sensor.clothes_dryer_running`, and `binary_sensor.dishwasher_running`.
- **Calibration Baseline Cutoff:** Formally calibrated on **August 22, 2026 at 17:13:00 UTC** (Panel 02) and **August 24, 2026 at 13:35:00 UTC** (Panel 01). Historical queries prior to these timestamps contain uncalibrated/inverted data; all whole-home ClickHouse analytics and baseline modeling should filter `timestamp >= '2026-08-24 13:35:00'`.

---

## 8. Audio, Media & Satellite Ecosystem
**Hardware:** Echo Show 5 (TECHO5 v1.2.6) at `10.0.10.161` (`Desk`), Echo devices, and Music Assistant.

- **Desk Smart Display Integration:** Connected via ESPHome / HA API as `Desk`.
    - **Live Doorbell Popups:** Automation `Security: Desk Echo - Doorbell Video on Person Detected` (`automation.security_desk_echo_doorbell_popup`) automatically pushes a 45-second live video feed (`camera.doorbell_outside_medium_resolution_channel`) via `esphome.desk_home_show_camera` whenever person activity or doorbell presses occur while `input_boolean.camera_alerts` is active.
    - **Music Assistant & Audiobookshelf Tracking:** Linked as `media_player.desk` within Music Assistant. Configured with Audiobookshelf provider for bidirectional audiobook progress synchronization. On-screen controls, album art, and transport states follow playback dynamically via `select.desk_now_playing_follows` set to `media_player.desk`.

---

## 9. Analytics & Infrastructure
- **ClickHouse Pipeline:** Whole-home high-frequency telemetry is streamed continuously into a local ClickHouse instance (`127.0.0.1:8124`) by `ha_telemetry_exporter`. ClickHouse maintains over 25M+ rows of historical telemetry across `home_assistant_data.whole_home_telemetry` and `home_assistant_data.climate_analytics` with sub-millisecond query execution.
- **COP-Based Multi-Zone HVAC Health Engine (`bin/hvac_health_check.py`):** Runs daily to evaluate real-time cooling efficiency across Upstairs (Panel 01 Cir 3), Downstairs (Panel 02 Cir 3) Trane heat pumps, and the Office Mini-Split. Queries ClickHouse directly via HTTP using Python's standard library (`urllib.request`) with zero external virtualenv dependencies. Segments discrete cooling sessions ($P > \text{min\_run\_power}$, $\text{duration } 8\text{–}90\text{ min}$, $\Delta T \ge 0.3^\circ\text{F}$), extracts temperature drops ($\Delta T$) and outdoor ambient temperatures, and computes true electrical energy consumed per degree drop ($\text{kWh / } ^\circ\text{F}$). Exposes structured JSON telemetry to `sensor.hvac_health_status`.
- **Local ClickHouse Analytics Tooling (`skills/ch_analytics.py`):** Provides instant SQL execution and pre-compiled diagnostic presets (`energy`, `asymmetry`, `entities`) against the local ClickHouse database with zero third-party dependencies.
- **Docker Management:** Container control is handled via `curl` to the `socket-proxy` Docker API.
- **Sim Lab:** A Digital Twin environment (`integrations/sim_lab.yaml`) used to stress-test logic against 10 specific scenarios (e.g., Short-Cycle, Type Mismatch, High Humidity) before deployment.

---

## 10. Diagnostic Cheat Sheet
- **Climate Check:** `grep "PHASE_" climate_control_log.csv | tail -n 20`
- **ClickHouse Analytics:** `python3 skills/ch_analytics.py --preset energy` or `--preset asymmetry`
- **HVAC Health Telemetry:** `python3 bin/hvac_health_check.py`
- **Docker Status:** `curl -s http://127.0.0.1:2375/containers/ha_telemetry_exporter/json | jq .State.Status`
- **Config Check:** `ha core check` or `docker exec hass hass --script check_config -c /config`

---

## 11. Custom Agent Skills Suite
To empower programmatic, local, and secure AI-agent operations, the system deploys a suite of local Python-executable tools in the `skills/` directory. These tools are designed with zero external host-level dependencies to execute natively on the host's standard Python interpreter (`/usr/bin/python3`), while utilizing secure credential parsing or container-delegation pathways for privileged operations.

### Component Map

#### A. HA REST API Client (`skills/ha_client.py`)
A lightweight, programmatic REST client that extracts Bearer Tokens and internal endpoints dynamically from workspace `.agents/mcp_config.json` and user configurations. This tool interacts directly with Home Assistant's state engine and services.
* **Usage - Fetch State:** `python3 skills/ha_client.py get sensor.bedroom_temperature_smoothed`
* **Usage - Call Action:** `python3 skills/ha_client.py action light turn_on '{"entity_id": "light.bedroom_ceiling"}'`

#### B. Jinja Sandbox Compiler (`skills/jinja_sandbox.py`)
A secure sandboxed parsing and compilation engine that compiles arbitrary Jinja templates using Home Assistant's native `/api/template` REST endpoint. This ensures accurate type evaluation and system variable lookups without running local sandbox parsers.
* **Usage:** `python3 skills/jinja_sandbox.py "{{ states('sensor.bedroom_temperature_smoothed') | float }}"`

#### C. Log Diagnostic & Performance Compiler (`skills/log_parser.py`)
A streaming parser that scans `climate_control_log.csv` and `home-assistant.log`. It isolates core events (`PHASE_`), highlights climate exceptions, and compiles system warnings into formatted CLI tables.
* **Usage - Warnings Scan:** `python3 skills/log_parser.py warnings`

#### D. ClickHouse Telemetry Analytics Engine (`skills/ch_analytics.py`)
A high-speed analytics script querying the local ClickHouse instance at `127.0.0.1:8124` using Python standard library HTTP requests.
* **Usage - Presets:** `python3 skills/ch_analytics.py --preset asymmetry` (or `energy`, `entities`)
* **Usage - Raw SQL:** `python3 skills/ch_analytics.py "SELECT count() FROM home_assistant_data.whole_home_telemetry"`

#### E. Sim Lab Scenario Runner & Learning Auditor (`skills/run_sim_lab.py`)
An automation runner that triggers digital twin scenarios in the Sim Lab (`script.run_climate_stress_tests`) and audits repository learning state transitions (`input_text.sim_mbr_repo`) to verify math and adaptive learning velocity changes after simulation runs.
* **Usage:** `python3 skills/run_sim_lab.py --scenario 1`

