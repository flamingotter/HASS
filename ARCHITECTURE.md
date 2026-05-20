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

## 3. MBR Climate Engine (v7.8.4)
A high-precision engine designed to reach sleep temperature exactly at bedtime.

- **Data Repository:** `input_text.mbr_cooling_performance_data` (JSON). Stores min/deg cooling rates in 5-degree outdoor bins.
- **Single-Pass Clean-Sweep Pattern:** Consolidated logic (Load -> Normalize -> Lookup -> Math -> Merge) inside a single Jinja block to eliminate duplicate keys and type-drift.
- **Safety-First Handoff:** Thermostat reset to maintenance target occurs at the **absolute start** of Phase 3. This ensures that even if learning math or AI co-processing fails, the home remains at a safe temperature.
- **Atomic Lock (Mode: Queued):** The automation uses `mode: queued`. Because the thermostat is reset first in Phase 3, any subsequent "zombie" triggers in the queue will find the state no longer matches the "Agonal Push" requirement (T6 target is no longer 60°F) and stop safely—preventing duplicate runs. This mode ensures that 7:00 AM wakeup and AI evaluations are not interrupted by sensor jitter.
- **Phases:**
    1. **Wakeup:** Reset to 68°F.
    2. **Strategist (7:00 PM):** AI evaluates "Free Cooling" via patio door.
    3. **Pre-Cooling:** Aggressive push to 60°F based on bin math + AI Humidity Optimizer.
    4. **Handoff:** At target, reset T6 Pro to maintenance temp. AI Auditor validates session data.
- **Data Armor:** A software physical-swing cap (±5 min/deg) protects the repository from sensor jitter or thermal anomalies.

---

## 4. Vision & Security Engine (v1.5)
**Authority:** `Security: Front Porch - AI Video Analysis`
Handles identity verification and suspicious activity detection.

- **Resilient Recording:** Uses `continue_on_error: true` for `camera.record` to survive DTS stream errors (caused by 5s GOP intervals found in camera hardware).
- **Sequential Processing:** Data collection (video/snapshots) must complete and include a 2s "Flush Delay" before AI analysis begins to prevent file-locking errors.
- **AI Context:** Uses MJ and Josh reference photos to identify residents vs. delivery personnel.

---

## 5. Analytics & Infrastructure
- **BigQuery Pipeline:** Data is exported to BigQuery for thermal decay and cooling velocity analysis.
- **Docker Management:** Container control is handled via `curl` to the `socket-proxy` Docker API.
- **Sim Lab:** A Digital Twin environment (`integrations/sim_lab.yaml`) used to stress-test logic against 10 specific scenarios (e.g., Short-Cycle, Type Mismatch, High Humidity) before deployment.

---

## 6. Diagnostic Cheat Sheet
- **Climate Check:** `grep "PHASE_" climate_control_log.csv | tail -n 20`
- **Simulation Validation:** `grep "SIM_DATA" home-assistant.log | tail -n 10`
- **Docker Status:** `curl -s http://127.0.0.1:2375/containers/ha_bq_exporter/json | jq .State.Status`
- **Config Check:** `ha core check` or `ha core restart`
