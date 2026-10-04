# Home Assistant Lab Context
- **Structure:** Modular Package-based config in `integrations/` and `entities/`.
- **Environment:** Docker container on Ubuntu 26.04.1 LTS host (kernel 7.0). Home Assistant 2026.9.2. Python 3.14.6 in container, Python 3.14.4 on host.
- **Paths:** Internal container path is `/config/`. External host path is `/opt/docker/appdata/hub/hass/`.
- **ClickHouse Analytics:** Replaced legacy BigQuery. All 25M+ rows of historical whole-home and climate telemetry migrated to local ClickHouse at `127.0.0.1:8124` (database `home_assistant_data`, tables `whole_home_telemetry` and `climate_analytics`). Continuous 60s ingestion streamed by `ha_telemetry_exporter`, hardened with rate-limiting watermarks (5m for cumulative daily energy, 15m for barometric pressure) to filter ~200k redundant rows/day.
- **AppArmor / Bluetooth:** `homeassistant` container configured with `security_opt: - apparmor:unconfined` in `/opt/docker/compose/home/compose.yaml` to grant full BlueZ D-Bus socket access on Ubuntu 26.04.

## 1. Documentation Map
- **[ARCHITECTURE.md](ARCHITECTURE.md):** Core logic engines, state machines, and cross-automation dependencies.
- **[CLIMATE_SUMMARY.md](CLIMATE_SUMMARY.md):** Historical evolution and detailed technical breakdown of the MBR Sleep Comfort Engine.
- **[ROADMAP.md](ROADMAP.md):** Active projects, pending infrastructure fixes, and planned feature expansions.

## 2. Primary Rules & Standards
- **Modern Syntax:** Always use `template:` integration, `action:` instead of `service:`, and `data:` for all templated values.
- **Persistence:** Avoid `initial:` values in YAML for entities that rely on `restore_state` (e.g., input_text/numbers).
- **UI-First Helper Provisioning:** Helper entities (`input_text`, `input_boolean`, `input_number`, `input_datetime`, `timer`) MUST be created via Home Assistant's internal collection WebSocket API (`<domain>/create` using `tools/manage_ui_helper.py` or `/opt/docker/secrets/hub/ha_mcp_token`) rather than YAML files. This ensures they are registered in `.storage/<domain>` and `core.entity_registry` as native, editable UI helpers (`"editable": true`).
- **Cleanup:** Ignore "missing" entities in `group.grow_shelf` or `group.echos`. Holiday entities (e.g., `light.led_tree`) are seasonal.
- **Integrity:** Do NOT remove or modify logic marked `enabled: false`.
- **Repository Management:** PERFORMANCE REPOS MUST use the "Single-Pass Clean-Sweep" pattern (v7.8.3+). Never pass dictionary variables between blocks; Home Assistant will re-parse and corrupt types. Perform Load, Normalize, Lookup, and Merge in a single atomic Jinja block.

## 3. Active Architectural Patterns
- **Authority -> Reactor:** For state-heavy logic (Presence, Alarm), centralize decisions in an "Authority" automation (e.g., `Person: Status Synchronizer`). Reactor automations should watch state changes and remain simple.
- **Fail-Safe AI:** Strategic LLM tasks (`ai_task`) must use `continue_on_error: true` and provide robust fallback defaults (`| float(target)`) to prevent system stalls.
- **Data Armor:** Always implement physical swing caps (e.g., ±5 min) and a 5-minute minimum duration gate for all climate learning sessions.
- **Whitespace Hardening:** Aggressively use `>-` and `{%- ... -%}` in all multi-line Jinja templates. Hidden newlines (`\n`) in variables cause string lookup failures and JSON duplication.

## 4. Global Constants & Identity
- **Users:**
    - **Josh:** `device_id: d818035824cf47ea` | `notify.mobile_app_josh_mobile`
    - **MJ:** `device_id: 0aa560faf0e8784c` | `notify.mobile_app_mj_pixel_8_pro`
- **Pets (The Felines):**
    - **Battle Cat:** (he/him)
    - **Josie:** (she/her)
    - **Custard:** (she/her)

## 5. Maintenance & Diagnostics
- **Diagnostics Tools:** Run ClickHouse analytics via `skills/ch_analytics.py` (presets: `energy`, `asymmetry`, `entities`).
- **Log Review:** Use `grep "PHASE_"` for Climate diagnostics or `grep "SIM_DATA"` for simulation results in `home-assistant.log`.
- **Simulation First:** ALL major logic changes (Climate, Presence) MUST be verified in `integrations/sim_lab.yaml` using the stress test script before production deployment.

## 6. Current System State (As of September 25, 2026)
- **Host Migration:** Successfully migrated to Ubuntu 26.04.1 LTS host. Docker AppArmor unconfined configured for `hass` to enable dual host Bluetooth adapters (`hci0`, `hci1`).
- **Telemetry Migration:** Fully migrated from Google BigQuery to local ClickHouse (`127.0.0.1:8124`). `hvac_health_check.py` upgraded to zero-dependency native ClickHouse HTTP query.
- **Climate Engine (v7.8.6):** Logic Certified stable. Uses sorted string-keyed JSON repository with Overrides/Attic sensors integrated.
- **Vision Engine (v1.5):** Resilient recording with 2s flush delay to survive DTS stream drift.
- **Security & Alarm State:** Staged aggregate watcher `binary_sensor.door_locks` checking the native `lock.door_locks` helper group, optimized sirens automations to prevent triggering during `armed_night` status, and hardened lock controls in Bedtime/Away automations with state filters to prevent Yale Assure 2 deadbolt-hanging issues.
- **Startup:** Zero-error boot verified on HA 2026.9.2. `sensor.last_alexa` guarded with `'defined'` filter.
