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
- **Phases:**
    1. **Wakeup:** Reset to 68°F.
    2. **Strategist (7:00 PM):** AI evaluates "Free Cooling" via patio door. Now humidity-aware: explicitly advises against opening if outdoor humidity > 65%.
    3. **Pre-Cooling:** Aggressive push to 60°F based on bin math + AI Humidity Optimizer.
    4. **Handoff:** At target, reset T6 Pro to maintenance temp. AI Auditor validates session data.
- **Data Armor:** A software physical-swing cap protects the repository from sensor jitter or thermal anomalies. **Raised to 60.0 min/deg** to accommodate extreme summer heat loads.
- **Bedtime Shift & Solar Pressure Relief (Added June 2026):** Shifting the sleep bedtime target to `23:30` (11:30 PM) places pre-cooling triggers later in the evening (typically 7:30 PM - 8:30 PM). This delays the start of the high-draw cycle until after solar radiation on the roof deck has subsided, bypassing peak attic heat-soak loads, enhancing thermal decay efficiency, and ensuring virtually 100% comfort target reliability.
- **Target Override Safeguard (Added June 2026):** To prevent accidental target temperature changes (such as slider touches while scrolling on mobile devices) from disrupting the active pre-cooling cycle, a state-recalculating safeguard was implemented. It monitors target temperature updates during pre-cooling, sends an actionable push notification with options to keep or revert the change, and handles the revert state statelessly using dynamic callback actions (REVERT_BEDROOM_TARGET_XX).
- **Attic Micro-Climate Sensors (Added June 2026):** Two physical dual-sensor arrays were integrated to capture real-time roof thermal loads:
    - **North Attic:** `sensor.north_attic_sensor_air_temperature` / `sensor.north_attic_sensor_humidity`. Covers the front porch, dining area, foyer, laundry, pantry, and north guest room. Mounted 2 feet above blown-in insulation, 1 foot below the roof deck.
    - **South Attic:** `sensor.south_attic_sensor_air_temperature` / `sensor.south_attic_sensor_humidity`. Covers the living room and downstairs master bedroom suite. Mounted 2 feet below the highest peak of the roofline.
    - **Physical Separation:** The two attic zones are separated by the second-floor hallway and office, with a small connecting space above the hallway.
- **Thermodynamic Solar Load Asymmetry (SLA):** Under midday solar exposure, an intense thermal gradient exists across the roof. Telemetry shows a 14.6°F asymmetric solar load delta between the South Attic (112.1°F) and the North Attic (97.5°F), creating a 45.6°F thermal conduction differential across the downstairs MBR ceiling (66.5°F indoor room temperature).
- **Roadmap to Climate Engine v7.9:** Mapped inside `exporter.py` for 7-day high-resolution BigQuery baseline profiling. Once complete, Scenario K (Attic Heat Soak Challenge) will validate the model in Sim Lab, allowing real-time attic thermal pressure to be used as a dynamic pre-cooling start-time multiplier.

---

## 4. Vision & Security Engine (v1.5)
**Authority:** `Security: Front Porch - AI Video Analysis`
Handles identity verification and suspicious activity detection.

- **Resilient Recording:** Uses `continue_on_error: true` for `camera.record` to survive DTS stream errors (caused by 5s GOP intervals found in camera hardware).
- **Sequential Processing:** Data collection (video/snapshots) must complete and include a 2s "Flush Delay" before AI analysis begins to prevent file-locking errors.
- **AI Context:** Uses MJ and Josh reference photos to identify residents vs. delivery personnel.

---

## 5. Analytics & Infrastructure
- **BigQuery Pipeline:** Data is exported to BigQuery for thermal decay and cooling velocity analysis. The `ha_bq_exporter` container is hardened with an infinite sleep loop (`sh -c "python exporter.py; exec sleep infinity"`) and set to `restart: unless-stopped`. This keeps the container permanently in a `Running` state to prevent it from being pruned by the weekly `docker system prune` of the housekeeper, while allowing Home Assistant to trigger the daily export cleanly via the `socket-proxy` restart command.
- **AI Agent Direct Query (Remote MCP):** To empower AI agents with direct, real-time analytics access, the official Google Cloud remote MCP server (`bigquery_remote`) is integrated client-side. This allows direct, credential-secured schema discovery and querying against the `moonlit-botany-293421` project's `home_assistant_data` dataset.
- **Docker Management:** Container control is handled via `curl` to the `socket-proxy` Docker API.
- **Sim Lab:** A Digital Twin environment (`integrations/sim_lab.yaml`) used to stress-test logic against 10 specific scenarios (e.g., Short-Cycle, Type Mismatch, High Humidity) before deployment.

---

## 6. Diagnostic Cheat Sheet
- **Climate Check:** `grep "PHASE_" climate_control_log.csv | tail -n 20`
- **Simulation Validation:** `grep "SIM_DATA" home-assistant.log | tail -n 10`
- **Docker Status:** `curl -s http://127.0.0.1:2375/containers/ha_bq_exporter/json | jq .State.Status`
- **Config Check:** `ha core check` or `ha core restart`
